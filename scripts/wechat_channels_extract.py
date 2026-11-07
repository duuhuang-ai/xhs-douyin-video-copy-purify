#!/usr/bin/env python3
"""Extract and transcribe one authorized WeChat Channels video into a new directory."""
import argparse
import json
import os
import shutil
import uuid
from pathlib import Path

import requests
from isaac64 import Isaac64


def decrypt(source: Path, destination: Path, key: int) -> None:
    with source.open('rb') as src, destination.open('xb') as dst:
        prefix = src.read(131072)
        stream = Isaac64(key).keystream(len(prefix))
        dst.write(bytes(a ^ b for a, b in zip(prefix, stream)))
        shutil.copyfileobj(src, dst)
    with destination.open('rb') as f:
        if b'ftyp' not in f.read(32):
            raise RuntimeError('解密结果未通过 MP4 基础检查，请核对视频和 decode_key 是否来自同一次响应。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('share_url', help='视频号分享链接')
    parser.add_argument('--work-dir', required=True, help='本次使用的全新目录（必须尚不存在）')
    args = parser.parse_args()
    key = os.environ['TIKHUB_API_KEY']
    api_base = os.environ.get('TIKHUB_API_BASE', 'https://api.tikhub.dev').rstrip('/')
    work = Path(args.work_dir).expanduser()
    work.mkdir(parents=True, exist_ok=False)
    session = requests.Session()
    response = session.post(api_base + '/api/v1/wechat_channels/v2/fetch_video_detail',
                            json={'share_url': args.share_url, 'raw': False},
                            headers={'Authorization': 'Bearer ' + key}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if payload.get('code') != 200:
        raise RuntimeError('TikHub 未返回成功结果，请检查接口权限、链接和服务状态。')
    data = payload['data']
    media = data.get('media') or {}
    url, decode_key = media.get('full_url'), media.get('decode_key')
    if not url or decode_key is None:
        raise RuntimeError('接口响应缺少视频地址或解密密钥。')
    encrypted, video = work / 'encrypted.mp4', work / 'decrypted.mp4'
    with session.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with encrypted.open('xb') as out:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    out.write(chunk)
    decrypt(encrypted, video, int(decode_key))

    import oss2
    import dashscope
    from dashscope.audio.asr import Transcription
    auth = oss2.Auth(os.environ['OSS_ACCESS_KEY_ID'], os.environ['OSS_ACCESS_KEY_SECRET'])
    bucket = oss2.Bucket(auth, os.environ['OSS_ENDPOINT'], os.environ['OSS_BUCKET_NAME'], connect_timeout=120)
    bucket.timeout = 900
    object_name = 'transcripts/wechat-' + uuid.uuid4().hex + '.mp4'
    bucket.put_object_from_file(object_name, str(video))
    signed_url = bucket.sign_url('GET', object_name, 86400)
    dashscope.api_key = os.environ['DASHSCOPE_API_KEY']
    task = Transcription.async_call(model='paraformer-v2', file_urls=[signed_url], language_hints=['zh', 'en'])
    if task.status_code != 200:
        raise RuntimeError('创建语音识别任务失败，请检查百炼服务和权限。')
    result = Transcription.wait(task=task.output.task_id, timeout=3600)
    if result.status_code != 200:
        raise RuntimeError('语音识别任务失败，请检查百炼服务和任务状态。')
    response = session.get(result.output['results'][0]['transcription_url'], timeout=120)
    response.raise_for_status()
    raw = response.json()['transcripts'][0]['text']
    (work / 'raw.txt').write_text(raw, encoding='utf-8')
    (work / 'meta.json').write_text(json.dumps({'title': data.get('title') or '视频号',
                                               'source_url': args.share_url,
                                               'oss_object': object_name}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'raw': str(work / 'raw.txt'), 'meta': str(work / 'meta.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
