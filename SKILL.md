---
name: 小红书抖音视频文案提纯
description: 将抖音/小红书视频链接、本地视频或原始文字稿一键提取文案并转写、提纯整理成可直接分享的干净原文，默认交付飞书文档（可按用户要求调整）。覆盖三类输入：平台链接自动提取+转写、本地视频/音频批量转写、纯文字稿直提纯。触发词：视频文案提纯、小红书抖音视频文案提纯、文案提纯、整理文字稿、结构化逐字稿、直播文字稿、短视频文字稿、播客文字稿、录音转写稿，或直接发送平台链接/本地视频。
---

# 小红书抖音视频文案提纯

## Prerequisites

Configure only the credentials needed for the chosen input. Text-only cleanup does not require TikHub, OSS or DashScope. The skill reads credentials from environment variables; never hardcode them.

```bash
# TikHub (platform video extraction)
export TIKHUB_API_KEY="your-key"
# API domain: use api.tikhub.dev for mainland China, api.tikhub.io for overseas

# Alibaba Bailian / DashScope (Paraformer-v2 ASR)
export DASHSCOPE_API_KEY="sk-your-key"

# Alibaba OSS (local video upload)
export OSS_ACCESS_KEY_ID="your-key"
export OSS_ACCESS_KEY_SECRET="your-secret"
export OSS_BUCKET_NAME="your-bucket-name"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
```

> **关于 Workspace ID**：百炼控制台"默认业务空间"下拉里的 ID 仅在调用百炼"应用 API"时使用（应用编排、智能体、工作流等）。本 skill 用的是 DashScope SDK 直接调用 Paraformer-v2 模型，**不需要 Workspace ID**。

If a credential is missing, explain which service needs it and how to configure it locally; never request that the user paste secrets in chat.

### Network routing notes

| Service | Network path | Notes |
|---|---|---|
| TikHub API | Connectivity varies by location and network | Check connectivity and provider documentation; do not change proxy settings without authorization |
| Alibaba OSS | Direct connection (domestic) | Use the configured network route; change proxy settings only when needed |
| DashScope (Paraformer-v2) | Direct connection (domestic) | Use the configured network route; change proxy settings only when needed |

The batch script bypasses proxy settings for its own process; verify this fits the environment before use.

## Input Modes & Routing

On receiving a user request, inspect the input and route to one of three modes:

### Mode A: Platform Link → Video → ASR → Purify

**Trigger**: The user sends a Douyin (`v.douyin.com`, `douyin.com/video/...`) or Xiaohongshu (`xiaohongshu.com/explore/...`, `xhslink.cn/`) share link.

**Step 1 — Extract video URL via TikHub**

Douyin:
```
GET https://api.tikhub.dev/api/v1/douyin/app/v3/fetch_one_video_by_share_url?share_url={url_encoded}
Authorization: Bearer {TIKHUB_API_KEY}
```
Response shape (key fields only):
```
data.aweme_detail.aweme_id
data.aweme_detail.desc                      # source title
data.aweme_detail.duration                  # milliseconds
data.aweme_detail.video.play_addr.url_list  # video CDN URLs (may be short-lived)
data.aweme_detail.video.bit_rate[*].gear_name + play_addr.url_list  # multi-bitrate options
```
Take `url_list[0]` from `play_addr` (standard quality is sufficient for ASR).

Xiaohongshu:
```
GET https://api.tikhub.dev/api/v1/xiaohongshu/app_v2/get_video_note_detail?share_text={url_encoded}
Authorization: Bearer {TIKHUB_API_KEY}
```
Extract the video URL from the response data. Look for `video_url` / `video` / play address fields.

**视频号（微信视频号）**：公开版暂不提供链接自动解密和提取。相关第三方解密依赖的再分发许可尚待核实；如用户已合法取得本地视频、音频或文字稿，可按 Mode B / C 处理。不要宣称链接自动提取已可用。

Both platforms use the same base domain. Replace with `api.tikhub.io` when user is overseas.

**Step 2 — Download video**

TikHub-extracted CDN URLs are **short-lived** (may expire within minutes). Download immediately after extraction. Route through proxy if TikTok API calls require it; video download can go direct.

```bash
# TikTok API calls: route through proxy (TikHub is Cloudflare-backed, blocked in mainland China)
curl -s --max-time 30 -G "https://api.tikhub.dev/api/v1/douyin/app/v3/fetch_one_video_by_share_url" \
  --data-urlencode "share_url={link}" \
  -H "Authorization: Bearer $TIKHUB_API_KEY" \
  -o /tmp/structured_transcript/tikhub.json

# Video download: add Referer header to bypass anti-leech
curl -s -L --max-time 120 \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://www.douyin.com" \
  -o "/tmp/structured_transcript/{aweme_id}.mp4" \
  "{video_url}"
```

Create `/tmp/structured_transcript/` if it does not exist. Keep intermediate files until the user authorizes deletion; explain where they are stored.

**Step 3 — Transcribe via Bailian Paraformer-v2**

Use the `dashscope` Python SDK. Upload to OSS under a unique object name and use a time-limited signed URL (TikHub CDN URLs may expire before asynchronous processing completes).

```python
import os
import oss2

# Upload downloaded video to OSS
auth = oss2.Auth(os.environ["OSS_ACCESS_KEY_ID"], os.environ["OSS_ACCESS_KEY_SECRET"])
bucket = oss2.Bucket(auth, os.environ["OSS_ENDPOINT"], os.environ["OSS_BUCKET_NAME"])
object_name = f"transcripts/{unique_run_id}/{aweme_id}.mp4"
bucket.put_object_from_file(object_name, local_video_path)
oss_url = bucket.sign_url("GET", object_name, 86400)
```

Then transcribe via Paraformer-v2:

```python
from dashscope.audio.asr import Transcription
from http import HTTPStatus
import dashscope
import requests
import json

dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]

task_response = Transcription.async_call(
    model='paraformer-v2',
    file_urls=['{OSS_URL}'],
    language_hints=['zh', 'en']
)

transcribe_response = Transcription.wait(task=task_response.output.task_id)
if transcribe_response.status_code == HTTPStatus.OK:
    # Step 1: fetch the transcription JSON from the result URL
    result_url = transcribe_response.output['results'][0]['transcription_url']
    asr_data = requests.get(result_url, timeout=30).json()

    # Step 2: extract text from transcripts[0].text
    transcript_text = asr_data['transcripts'][0]['text']

    # Optional: get sentence-level timestamps from asr_data['transcripts'][0]['sentences']
```

**Important**: Paraformer-v2 may misrecognize homophones (e.g. "AI" → "爱", "Excel" → "excel", "爆款" → "报款", "低粉" → "一份"). The purification step (Mode C) includes ASR cleanup rules to fix high-confidence recognition errors. Common fixes observed: 小红书电商←小魔书店商, 低粉←一份, 爆款←报款.

**Step 4 — Purify**

Proceed to Mode C with the raw ASR text.

---

### Mode B: Local Video → OSS → ASR → Purify

**Trigger**: User provides local video file path(s), or points to a folder of videos.

**Step 1 — Validate files**

Check that file(s) exist and are in a supported format (mp4, mov, avi, mkv, wav, mp3, flv, webm).

**Step 2 — Upload to OSS for public URL**

Bailian Paraformer-v2 requires a public HTTP URL. Upload each local video to OSS:

```python
import oss2

auth = oss2.Auth(os.environ["OSS_ACCESS_KEY_ID"], os.environ["OSS_ACCESS_KEY_SECRET"])
bucket = oss2.Bucket(auth, os.environ["OSS_ENDPOINT"], os.environ["OSS_BUCKET_NAME"])

object_name = f"transcripts/{unique_run_id}/{filename}"
bucket.put_object_from_file(object_name, local_path)
public_url = bucket.sign_url("GET", object_name, 86400)
```

Prefer a time-limited signed URL; do not change bucket access settings without explicit authorization. If the bucket is not public-read, use `bucket.sign_url('GET', object_name, 86400)` for a 24-hour signed URL.

> **⚠️ oss2 超时坑（实测踩过）**：`oss2.Bucket(...)` **不接受** `read_timeout` 关键字参数（只认 `connect_timeout`）。默认超时仅 60s，慢网络下上传会 `ReadTimeout` 崩溃。正确做法：`oss2.Bucket(auth, endpoint, bucket, connect_timeout=120)` 之后**再设 `bucket.timeout = 900`**（oss2 内部只用单一 timeout 值，这同时放大读写超时）。上传/转写务必加 3 次重试 + 退避，主循环包 per-video try/except，单视频失败记日志继续而非整批中断。

> **可选优化（实测有效）**：本机若没有系统级 `ffmpeg`，不必安装——在受管 venv 里 `pip install imageio-ffmpeg`，用 `imageio_ffmpeg.get_ffmpeg_exe()` 拿二进制即可。用 ffmpeg 先把视频抽成 mono 16k 的 mp3（`-vn -ac 1 -ar 16000 -b:a 64k`）再上传，能大幅缩小上传体积；**百炼 Paraformer-v2 直接吃压缩 mp3 没问题**，无需视频格式。注意 `dashscope` / `imageio-ffmpeg` 都要装进受管 venv；脚本涉及 OSS+DashScope 时设 `NO_PROXY=*` 绕开代理。

> **🔧 现成批量流水线脚本**：`scripts/batch_asr_pipeline.py` 已封装上述全部要点（去重 `(1)`/`( chuhai5.net )` 副本、按 `N.NN` 数字排序、oss2 超时加固、上传/转写重试、per-video 容错、24h 签名 URL、Paraformer-v2 异步转写）。用法：
> ```bash
> XHS_SOURCE_DIR="/path/to/videos" XHS_WORK_DIR="/path/to/new-work-dir" XHS_OSS_PREFIX="transcripts/unique-run-id" \
> OSS_ACCESS_KEY_ID=... OSS_ACCESS_KEY_SECRET=... OSS_BUCKET_NAME=... OSS_ENDPOINT=... \
> DASHSCOPE_API_KEY=... \
> python \
>   "<skill目录>/scripts/batch_asr_pipeline.py" [rebuild]
> ```
> 输出 `<WORK>/raw/<NN>.txt`（原始稿）、`<WORK>/manifest.json`（idx→path/title/chapter/tag）、`<WORK>/audio/<NN>.mp3`（临时音频，可删）。加 `rebuild` 强制重建清单；重跑会自动跳过已完成的视频。

> **⚠️ 复用旧 WORK 目录会静默转错视频（实测踩过，后果严重）**：脚本启动时不校验 manifest 与 `XHS_SOURCE_DIR` 是否匹配——只要 `<WORK>/manifest.json` 存在就直接复用，且发现 `raw/<NN>.txt` 已存在就 `continue` 跳过。因此若 `XHS_WORK_DIR` 指向一个**之前处理过别的视频**的目录，本轮会沿用旧清单里指向旧视频的 `path`，产出的 `raw/01.txt` 仍然是**上一个视频**的内容，日志却照样打印 `PIPELINE COMPLETE 1/1 failed=[]`，看起来完全成功。
>
> **每次处理新视频都必须换一个全新的 `XHS_WORK_DIR`**；不要覆盖已有项目的输出。跑完第一步先核对 `<WORK>/manifest.json` 里的 `path` / `title` 是否就是本次目标，再去提纯——不要只信 `PIPELINE COMPLETE`。

> **⚠️ 长视频分片的 seek 偏移坑（实测踩过，后果严重）**：部分录屏/直播回放 mp4 的**容器声明时长与实际音轨解码时长不一致**（实测一例：`ffmpeg -i` 报 3:19:45，把整段音轨重编码出来却是 3:37:08，差 8.7%）。此时直接对原视频用 `-ss/-t` 切片，ffmpeg 按容器时间基 seek、按实际解码时长输出，切点会整体偏移约 8%，两段时长都对不上预期，**而退出码照样是 0**，看起来完全成功。
>
> **正确做法（两步走）**：
> 1. 先用 ffmpeg 把整段音轨**一次性**重编码成 mp3（`-vn -ac 1 -ar 16000 -b:a 64k`，3.5 小时素材实测约 17 秒），得到时间戳规范的中间文件；
> 2. **再在 mp3 上做切片**（`-c copy` 即可，CBR 帧对齐，seek 精准）。
>
> 切完必须用 `ffmpeg -i` 回读每段 `Duration` 与预期核对，**不要只看退出码**。总时长按「整段 mp3 的实际时长」算，不按容器声明时长算。

> **🔗 分片重叠与合并**：分段之间留 8 秒重叠（如全片实长 13028s → part1 `[0, 6522]`、part2 `[6514, end]`）。ASR 在重叠区常有个别字差异（实测「热度达」vs「热度打」），不能用简单字符串相等匹配。用**最长前缀匹配**定位接缝：
> ```python
> for m in range(300, 10, -1):          # m 从大到小递减
>     pos = p1.rfind(p2[:m])            # p2 前缀在 p1 中最靠后的位置
>     if pos != -1 and pos > len(p1) * 0.9:
>         merged = p1[:pos] + p2        # 丢掉 p1 尾部重复段
>         break
> ```
> 合并后务必打印接缝上下文（前后各 80–120 字）人工核对通顺，再进入提纯。

**Step 3 — Transcribe via Bailian Paraformer-v2**

Same as Mode A Step 3, using the OSS public URL.

> **⚠️ raw 转写稿是单行超长文本，直接 Read 会被静默截断（实测踩过）**：Paraformer 输出整篇没有换行，`raw/01.txt` 全文就是一行。Read 工具对超长单行会静默截断——只读到开头一小段、不报错，极易误以为已读完全文。注意 Read 的「最多 2000 行」限制的是行数不是字符数，一行几万字的文件照样截。

> **正确做法（两步落盘）**：
> 1. 先按 `[。！？]` 切句，**每句末尾真的加换行 `\n` 再落盘**——只切句不加换行，落盘仍是单行，Read 照样截断（二次坑，实测踩过）；
> 2. 再按 ~4500 字符分块落盘（如 `chunks/chunk_01.txt`），逐块 Read，全部读完再开始提纯。
>
> 实测参考：431 句、最长单句 118 字符，分 4 块（4195/4176/4187/2342 字符）完整读出。落盘后用 `wc -c` 核对各块总字符数与原文一致，确认没丢内容。

**Step 4 — Purify**

Proceed to Mode C with the raw ASR text.

**Batch handling**: For multiple videos in a folder, process serially (one at a time, due to Bailian QPS limits). After all are transcribed, merge transcripts into a single document organized by video, then purify as one document.

---

### Mode C: Raw Text → Purify

**Trigger**: User provides raw transcript text, a text file, or asks to tidy an existing transcription.

This is the original skill workflow. Follow the purification rules below directly.

#### Mode C 子类型：本机录音／会议转写稿（带时间戳，单机文件）

**Trigger**：用户给的是本地 `.md` / `.txt` 文件，开头有录音时间（如 `2026年9月15日 15:21`），正文以 `MM:SS` 纯时间戳行分段，通常是线下沟通、电话、会议的转写稿（可能是双人或多人对话）。

**Step 1 — 去时间戳、量体**：用正则剔掉时间戳行再统计正文量级，别凭感觉估长度：

```python
import re
lines=[l for l in s.split('\n')
       if not re.fullmatch(r'\d{2}:\d{2}', l.strip())
       and not re.fullmatch(r'\d{4}年\d+月\d+日 \d{2}:\d{2}', l.strip())]
char_count = len(re.findall(r'[\u4e00-\u9fff]', ''.join(lines)))
```

**Step 2 — 判断分节方式**：
- **无说话人标签的双人商务对话**（最常见的形态）：**不要按人分 `##`**。对话来回交错、每段都换人，按人分会把同一主题撕成几十块，反而读不懂。正确做法是**按主题分 `##`**（一场 50 分钟的商务沟通通常 5-6 个主题），段落内保留原话的「我这边 / 你们那边」视角，读者自能分辨谁在说，**不要强行加「A 说 / B 说」标签**。
- 有明确说话人标签时，按上面「飞书妙记」子类型的规则处理。

**Step 3 — 清理口径（对话稿特有）**：删掉口语应答（`对对对` / `嗯` / `是的`）、填充词（`说白了` / `你知道吗` / `这个这个`）、自我修正的重叠（`我我我`）、听不清的模糊指代短语（**直接删，不要猜词**）。保留案例、数字、专有打法、双方的交涉立场。

**Step 4 — ASR 专有名词修正（高置信才改）**：实测高频错认——`抖音罗盘`←楼盘、`快手磁力通`←信意通、`Seedance`←生dance、`WorkBuddy`←work八、`飞书`←飞速、`RPA`←RP、`ROI`←RY/ROY。**客户名、主播名、品牌名、公司名一律原样保留**（如「慕江南」「一米鲜奶」「杉山小镇」这类），不确认的不猜，但可在交付说明里提一句「专有名词按原音保留」。

> **⚠️ 不要边读边改**：一份 1.5 万字的对话稿必须**先完整读一遍**（或先落盘分块读），再动笔整理；只看开头就开写必然丢后半程的内容。

#### Mode C 子类型：飞书妙记「文字记录」文档链接

**Trigger**: 用户发的是 `*.feishu.cn/docx/<token>`，抓下来是妙记导出的直播/会议文字记录（标题形如「文字记录：直播回放-MM月DD日」）。这类稿子**不需要 ASR**，直接走提纯。

**Step 1 — 抓内容**：`lark-cli docs +fetch --doc <token> --as user > /tmp/src_doc.json`，正文在 `data.document.content`（单行超长 XML，只有 `<title>/<p>/<br>/<blockquote>/<a>`）。用 Python 按 `<p>` 切段、`<br/>` 转换行、`html.unescape` 反转义后落盘，**不要直接打印**（Bash 输出会截断）。

**Step 2 — 去掉说话人与时间戳，按人合并**：妙记稿每行是 `说话人 N HH:MM:SS` + 内容。用正则 `^说话人\s*(\d)\s*(\d{2}:\d{2}:\d{2})\s*(.*)$` 解析成 (speaker, time, text)，再**合并同一说话人的连续段**（实测 274 段 → 166 段），这样读起来才有上下文。合并后统计每个说话人的字数，判断谁主讲、谁只是插话（插话者往往只占几千字）。

**Step 3 — 分块读全文**：Read 单次上限约 20k token，60k 字的稿子**必须按 ~14,500 字在段落边界切块**再逐块读。不读完就提纯必定丢内容。

**提纯要点（直播稿特有）**：
- **说话人标签要删**，但**多嘉宾稿要按人分 `##`**，用内容主题命名章节（如「一、小红书矩阵：从选题到发布的内容工作站」），不要用「嘉宾一/二/三」这种垃圾桶标题。
- **主持人话术要分层删**：拉互动、福袋、售卖/催单、名额倒计时、下期预告、关注引导 → 全删；他做的实质补充（概念解释、跨嘉宾总结）→ 保留，就近并入对应嘉宾的章节。
- **不要单开「共同方法论/总结」章节**。跨嘉宾提炼等于加了解读，违反「不加外部信息、不改写」的提纯纪律。
- 演示视频/录音里播放的口播内容（往往是另一个"说话人"、只有几段），标成「产出示例」保留一段即可。

---

## Purification Rules

Default output: **提纯版原文** — not a summary, not a raw transcript.

The document structure:
1. **来源行（仅 Mode A/B）**：对平台链接或本地视频，文档顶部先附来源——平台视频用 `> **来源**：[原标题]（原链接）`；本地视频用 `> **来源**：本地视频 <文件名>`。

> **⚠️ 本地视频只写文件名，不要写完整绝对路径**。飞书文档是要分享给学员/客户的，`/Users/<用户名>/Downloads/...` 这类路径会暴露 macOS 用户名和本机目录结构。正确写法是 `> **来源**：本地视频 25.12.16【曹菲】活用投放撬动千万曝光.mp4`，既方便核对原文又不泄漏信息。
2. `# 标题` — derived from the video title, topic, or source name
3. Optional one-line 整理说明 only when useful（如"原始 ASR 转写已去噪，修正同音词：低粉→一份、小魔书店商→小红书电商"）
4. A small number of large `##` themes
5. Specific `###` subheadings under each theme
6. Cleaned original-style paragraphs under each subheading

Forbidden sections: `一句话总结`, `核心要点`, `启发`, `结论`, `重点摘要`, `其他有效观点`, `补充内容`, `杂项`.

### What to remove
- Timestamps, speaker labels, greetings, waiting-room chatter, screen-sharing talk
- Repeated audience checks, off-topic banter
- Filler words, stutters, duplicated phrases, sentence fragments
- Obvious live-room noise and ASR artifacts

### What to keep
- Original meaning, tone, key judgments
- Cases, examples, numbers, analogies
- The full argument chain
- Important original wording and signature phrases
- For short videos: hooks, punchlines, rhythm, transitions, call-to-action
- For podcasts: conversational flow, disagreements, topic transitions

### What NOT to do
- Do NOT add facts, external information, or interpretation
- Do NOT rewrite into a new article — it should still read like the speaker
- Do NOT bold every paragraph — only bold important judgments, strong quotes, and concrete principles
- Do NOT invent timestamps or speaker labels

### Heading rules
- Use concrete headings describing the actual content discussed
- Use a few large themes (typically 2–5 `##` sections), not dozens of fragments
- No garbage-bin headings

### ASR cleanup
- Fix obvious speech-recognition errors only with high confidence
- Standardize recurring product/tool names only when the intended name is clear
- Add punctuation and paragraph breaks naturally

---

## Delivery: Feishu Doc

By default, deliver purified transcripts as Feishu documents when the user requests a transcript. Respect the user’s chosen output location and authorization. When delivering a Feishu document, provide its link and a concise description; respect any other output format the user requests.

Use an available Feishu document tool, such as `lark-cli` and the `lark-doc` skill when available, to create a new Feishu doc with the purified Markdown content. If unavailable, explain the limitation and provide a local draft. The doc title should be the same as the `# 标题`.

> **⚠️ 长文本传参坑（实测踩过）**：`docs +create --content @file` 的 `@file` **只接受 cwd 下的相对路径**，传 `@/tmp/xx.md` 会报 `unsafe file path`；也不要把提纯稿写进用户的工作目录只为了满足这个限制。正确做法是走 stdin：
> ```bash
> lark-cli docs +create --doc-format markdown --as user \
>   --title "文档标题" --content - < /tmp/xx.md
> ```
> 传参前把 md 正文里的 `# 标题` 行去掉（标题走 `--title`），否则飞书文档标题 + 正文一级标题会重复。创建后用 `docs +fetch --doc <token> --doc-format markdown` 回查中文字符数与 `##` 章节列表，确认没被截断再交付。

When a Feishu document is created, provide a clickable link, title and approximate word count; note material transcription uncertainty or cleanup.

> **改文档标题（常见后续操作）**：`lark-doc` 的 `docs +update` 只能改正文，**改不了文档标题**。改标题走 Drive 文件接口：
> ```bash
> lark-cli api PATCH /open-apis/drive/v1/files/{doc_id} \
>   --params '{"type":"docx"}' --data '{"new_title":"新标题"}'
> ```
> `doc_id` 即文档 token（URL 里 `docx/` 后的那段）。改完用 `lark-cli api GET /open-apis/docx/v1/documents/{doc_id}` 回查 `document.title` 确认。`docx/v1/documents` 的 PATCH 接口会报 `invalid param`，别走那条路。

---

## Quality Bar

Before finalizing, confirm:
- **来源行已附在文档顶部**（Mode A: 标题+原链接；Mode B: 本地文件名）
- Source meaning and argument order are preserved
- Output is not a summary, checklist, or commentary
- Greetings, filler, repetition, timestamps, speaker labels, and fragments are removed
- Key judgments, examples, numbers, analogies, and important original phrases remain
- Headings are specific and limited to real themes
- Bold text highlights high-value content without over-marking
- Feishu doc has been created (or local fallback is clearly noted)
- **Chat reply** is one-liner only: doc link + title + word count, no full text dump
