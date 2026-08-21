# 小红书抖音视频文案提纯

把抖音 / 小红书视频链接、本地视频 / 音频、或原始文字稿，一键**提取 → 转写 → 提纯**成可直接分享的干净原文，并自动交付飞书文档。

> 产出是「**提纯版原文**」——保留原意、论证链、案例与金句的干净稿，**不是摘要、也不是改写**。

---

## 功能介绍

本 Skill 是一条自动化流水线，覆盖「口语 / 视频内容 → 可分享原文」的完整链路：

- **三种输入形态，统一处理**
  - 模式 A：抖音 / 小红书分享链接 → 提取视频 → 转写 → 提纯
  - 模式 B：本地视频 / 音频文件（或文件夹批量）→ 转写 → 提纯
  - 模式 C：已有原始文字稿 / 转写稿 → 直接提纯
- **提取 + 转写 + 提纯一体化**
  - 用 TikHub 解析平台分享链接、拿到视频播放地址
  - 上传阿里云 OSS 换取稳定公开 URL，避免平台 CDN 短命链接导致转写失败
  - 用阿里云百炼 DashScope 的 **Paraformer-v2** 做 ASR 语音转文字（支持中英文）
  - 对原始转写稿做「提纯」整理
- **提纯而非总结**：保留原意、语气、关键判断、案例、数字、类比、论证链与金句；去除口语填充词、ASR 同音错误、时间戳、说话人标签、直播噪音。
- **自动交付飞书文档**：用 `lark-doc` 把提纯稿创建为飞书文档，对话区只回链接 + 一行说明，不贴全文。

---

## 适用场景

- 抖音 / 小红书爆款视频 → 提取文案做选题拆解、二次创作素材
- 直播回放、播客、短视频 → 转逐字稿并提纯成可分享原文
- 已有文字稿 / 录音转写稿 → 直接整理成干净原文

---

## 目录结构

```
.
├── SKILL.md                            # Skill 定义与完整操作规范（本 README 的权威来源）
├── agents/
│   └── openai.yaml                     # OpenAI Agent 兼容配置（display_name / short_description）
├── scripts/
│   ├── batch_asr_pipeline.py           # 本地视频批量 ASR 转写流水线
│   └── build_structured_transcript.py  # 提纯稿 → 飞书文档构建
└── README.md
```

---

## 快速安装（Codex / WorkBuddy）

把下面这段命令复制到 **Codex** 或 **WorkBuddy** 的终端执行即可（目录名即 Skill 名，必须保持中文 `小红书抖音视频文案提纯`）：

```bash
git clone https://github.com/duuhuang-ai/xhs-douyin-video-copy-purify.git ~/.workbuddy/skills/小红书抖音视频文案提纯
```

执行后**重载 / 重启会话**，Skill 即以「小红书抖音视频文案提纯」生效。

> **Codex 用户**：把目标路径换成 Codex 的 skills 目录即可（目录名不变）。
> 本仓库为**扁平结构**（Skill 文件直接在根目录），无需再套子文件夹；复制后整个仓库目录就是 Skill 目录。

---

## 配置前置依赖

Skill 通过环境变量读取凭证，**切勿硬编码**。

| 变量 | 用途 |
|---|---|
| `TIKHUB_API_KEY` | TikHub API，解析抖音 / 小红书分享链接、提取视频地址（国内 `api.tikhub.dev`，海外 `api.tikhub.io`） |
| `DASHSCOPE_API_KEY` | 阿里云百炼 DashScope，调用 Paraformer-v2 做 ASR 转写 |
| `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` | 阿里云 OSS，上传本地视频换取稳定公开 URL |
| `OSS_BUCKET_NAME` | OSS 桶名（默认 `hermes-videos`） |
| `OSS_ENDPOINT` | OSS Endpoint（默认 `oss-cn-hangzhou.aliyuncs.com`） |

> **不需要百炼 Workspace ID**：本 Skill 直接用 DashScope SDK 调 Paraformer-v2，不走「应用 API」（应用 API 才需要业务空间 ID）。

运行脚本的 Python 需安装：`oss2`、`dashscope`、`requests`、`imageio-ffmpeg`。

### 网络路由

| 服务 | 网络路径 | 备注 |
|---|---|---|
| TikHub API | 需代理 / VPN（Cloudflare，国内直连被挡） | Python `requests` 超时则用 `curl` 经 Bash |
| 阿里云 OSS | 直连（国内） | 脚本设 `NO_PROXY=*` 绕开代理 |
| 百炼 DashScope | 直连（国内） | 脚本设 `NO_PROXY=*` 绕开代理 |

当脚本只触碰 OSS + DashScope 时，前置 `NO_PROXY=*` 可避免无谓代理跳转导致的超时。

---

## 使用方式

### 触发词

`视频文案提纯`、`小红书抖音视频文案提纯`、`文案提纯`、`整理文字稿`、`结构化逐字稿`、`直播文字稿`、`短视频文字稿`、`播客文字稿`、`录音转写稿`，或直接发送平台链接 / 本地视频。

---

### 模式 A：平台链接 → 视频 → ASR → 提纯

**触发**：用户发抖音（`v.douyin.com`、`douyin.com/video/...`）或小红书（`xiaohongshu.com/explore/...`、`xhslink.cn/`）分享链接。

**Step 1 — 用 TikHub 提取视频地址**

抖音：
```
GET https://api.tikhub.dev/api/v1/douyin/app/v3/fetch_one_video_by_share_url?share_url={url_encoded}
Authorization: Bearer {TIKHUB_API_KEY}
```
关键返回字段：`data.aweme_detail.video.play_addr.url_list[0]`（取标准清晰度即可，CDN 链接短命，需立即下载）。

小红书：
```
GET https://api.tikhub.dev/api/v1/xiaohongshu/app_v2/get_video_note_detail?share_text={url_encoded}
Authorization: Bearer {TIKHUB_API_KEY}
```
从返回里取 `video_url` / `video` / 播放地址字段。海外用户把域名换成 `api.tikhub.io`。

**Step 2 — 下载视频**（CDN 链接数分钟内过期，提取后立即下载；加 `Referer` 破防盗链）
```bash
curl -s -L --max-time 120 \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://www.douyin.com" \
  -o "/tmp/structured_transcript/{aweme_id}.mp4" "{video_url}"
```

**Step 3 — 上传 OSS 换取稳定公开 URL，再用 Paraformer-v2 异步转写**
```python
import os, oss2
auth = oss2.Auth(os.environ["OSS_ACCESS_KEY_ID"], os.environ["OSS_ACCESS_KEY_SECRET"])
bucket = oss2.Bucket(auth, os.environ["OSS_ENDPOINT"], os.environ["OSS_BUCKET_NAME"])
object_name = f"transcripts/{aweme_id}.mp4"
bucket.put_object_from_file(object_name, local_video_path)
oss_url = f"https://{os.environ['OSS_BUCKET_NAME']}.{os.environ['OSS_ENDPOINT']}/{object_name}"
```
```python
import os, dashscope, requests
from dashscope.audio.asr import Transcription
from http import HTTPStatus
dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]
task = Transcription.async_call(model='paraformer-v2', file_urls=[oss_url], language_hints=['zh','en'])
resp = Transcription.wait(task=task.output.task_id)
if resp.status_code == HTTPStatus.OK:
    result_url = resp.output['results'][0]['transcription_url']
    asr = requests.get(result_url, timeout=30).json()
    transcript_text = asr['transcripts'][0]['text']   # 原始转写文本
```

> **Paraformer-v2 同音词坑**：可能把 "AI" 识别成 "爱"、"Excel" 成 "excel"、"爆款" 成 "报款"、"低粉" 成 "一份"。提纯步骤（模式 C）会按高置信度规则修正。常见修正：小红书电商←小魔书店商、低粉←一份、爆款←报款。

**Step 4 — 进入提纯**（见下方「提纯规则」）。

---

### 模式 B：本地视频 / 音频 → OSS → ASR → 提纯

**触发**：用户给本地文件路径，或指向一个装了视频的文件夹。

1. 校验文件存在且格式受支持（mp4 / mov / avi / mkv / wav / mp3 / flv / webm）。
2. 上传 OSS（桶设为公开读，或用 24h 签名 URL：`bucket.sign_url('GET', object_name, 86400)`）。
3. 用 Paraformer-v2 转写（同模式 A Step 3）。
4. 多视频**串行**处理（百炼有 QPS 限制），全部转写后合并为一个文档再提纯。

> **oss2 超时坑（实测踩过）**：`oss2.Bucket(...)` **不接收** `read_timeout` 参数（只认 `connect_timeout`），默认 60s 慢网会 `ReadTimeout`。正确做法：`oss2.Bucket(auth, endpoint, bucket, connect_timeout=120)` 之后**再设 `bucket.timeout = 900`**（oss2 内部只用单一 timeout 值，这会同时放大读写超时）。上传 / 转写务必加 3 次重试 + 退避，主循环包 per-video try/except，单视频失败记日志继续而非整批中断。

> **本机无 ffmpeg 也能跑**：在受管 venv 里 `pip install imageio-ffmpeg`，用 `imageio_ffmpeg.get_ffmpeg_exe()` 拿二进制；先把视频抽成 mono 16k 的 mp3（`-vn -ac 1 -ar 16000 -b:a 64k`）再上传，大幅缩小体积，百炼 Paraformer-v2 直接吃压缩 mp3 没问题。

**现成批量脚本**（`scripts/batch_asr_pipeline.py` 已封装上述全部要点：去重副本、`N.NN` 排序、oss2 超时加固、上传 / 转写重试、per-video 容错、24h 签名 URL、Paraformer-v2 异步转写）：
```bash
XHS_SOURCE_DIR="/path/to/videos" XHS_WORK_DIR="/tmp/xhs3" \
OSS_ACCESS_KEY_ID=... OSS_ACCESS_KEY_SECRET=... OSS_BUCKET_NAME=... OSS_ENDPOINT=... \
DASHSCOPE_API_KEY=... \
PYTHON scripts/batch_asr_pipeline.py [rebuild]
```
其中 `PYTHON` 为已安装 `oss2`/`dashscope`/`requests`/`imageio-ffmpeg` 的 Python 解释器。加 `rebuild` 强制重建清单；重跑会自动跳过已完成视频。输出 `<WORK>/raw/<NN>.txt`（原始稿）、`<WORK>/manifest.json`（idx→path/title/chapter/tag）、`<WORK>/audio/<NN>.mp3`（临时音频，可删）。

---

### 模式 C：纯文字稿 → 提纯

**触发**：用户直接给原始转写文本、文本文件，或要求整理已有转写稿。这是最原始的 Skill 工作流，直接套用下方提纯规则。

---

## 提纯规则（核心）

默认产出：**提纯版原文**——不是摘要、不是原始转写稿。

**文档结构**
1. **来源行（仅模式 A/B）**：顶部先附来源——平台视频用 `> **来源**：[原标题]（原链接）`，本地视频用 `> **来源**：本地视频路径`，方便跳转核对原文。
2. `# 标题`——取自视频标题 / 主题 / 来源名。
3. 可选一行整理说明（如"原始 ASR 转写已去噪，修正同音词：低粉→一份、小魔书店商→小红书电商"）。
4. 少量大 `##` 主题（通常 2–5 个）。
5. 每个主题下 `###` 子标题。
6. 子标题下干净的原文风段落。

**禁止章节**：`一句话总结`、`核心要点`、`启发`、`结论`、`重点摘要`、`其他有效观点`、`补充内容`、`杂项`。

**要删除**：时间戳、说话人标签、寒暄、等待期闲聊、屏幕共享讲解、重复的观众互动、跑题插科、填充词、口吃、重复短语、句子碎片、明显的直播噪音与 ASR 噪点。

**要保留**：原意、语气、关键判断；案例、例子、数字、类比；完整论证链；重要的原话与签名句式；短视频的钩子、金句、节奏、转场、行动号召；播客的对话流、分歧、话题切换。

**不要做**：
- 不要添加事实、外部信息或解读
- 不要改写成一篇新文章——读起来仍应像说话者本人
- 不要每段都加粗——只加粗重要判断、强引用、具体原则
- 不要编造时间戳或说话人标签

**标题规则**：用描述实际内容的具象标题；用少量大主题（2–5 个 `##`），不要几十个碎片；不设"垃圾筐"标题。

**ASR 清理**：仅在高置信度下修正明显语音识别错误；只在意图明确时统一反复出现的产品 / 工具名；自然地补标点与分段。

---

## 交付飞书文档

所有提纯稿都交付为**飞书文档**。不要把全文贴在对话里——只发飞书文档链接 + 一行简要说明（标题 + 字数）。

用 `lark-doc` Skill 以提纯后的 Markdown 内容新建飞书文档，文档标题同 `# 标题`。

在面向用户的回复里：
1. 只发飞书文档 URL（可点击链接）
2. 一行："已交付飞书文档——《标题》，约 N 字"
3. 若 ASR 清理较多（同音词修正、去噪），在同一行简要说明

> **改文档标题（常见后续）**：`lark-doc` 的 `docs +update` 只能改正文，**改不了文档标题**。改标题走 Drive 文件接口：
> ```bash
> lark-cli api PATCH /open-apis/drive/v1/files/{doc_id} \
>   --params '{"type":"docx"}' --data '{"new_title":"新标题"}'
> ```
> `doc_id` 即文档 token（URL 里 `docx/` 后的那段）。改完用 `lark-cli api GET /open-apis/docx/v1/documents/{doc_id}` 回查 `document.title` 确认。`docx/v1/documents` 的 PATCH 接口会报 `invalid param`，别走那条路。

---

## 质量门禁（交付前自检）

- [ ] 来源行已附在文档顶部（模式 A：标题 + 原链接；模式 B：本地路径）
- [ ] 原意与论证顺序保留，产出非总结 / 清单 / 评论
- [ ] 寒暄、填充词、重复、时间戳、说话人标签、碎片已去除
- [ ] 关键判断、案例、数字、类比、重要原话保留
- [ ] 标题具体、限于真实主题
- [ ] 加粗克制（只标高价值内容）
- [ ] 飞书文档已创建（或已注明本地兜底）
- [ ] 对话回复仅一行（链接 + 标题 + 字数），不贴全文

---

## 注意事项

### 网络路由
见上方「配置前置依赖 → 网络路由」。TikHub 需代理；OSS 与 DashScope 直连时脚本设 `NO_PROXY=*`。

### oss2 超时
见「模式 B」中的 oss2 超时坑说明。

### ASR 同音词（常见修正）
小红书电商←小魔书店商、低粉←一份、爆款←报款；以及 AI→爱、Excel→excel 等英文识别错误。

---

## License

未指定许可证。如需用于生产，请自行评估或联系作者。
