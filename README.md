# 小红书抖音视频文案提纯

把抖音/小红书视频链接、本地视频/音频、或原始文字稿，一键**转写 + 提纯**成可直接分享的干净原文，并自动交付飞书文档。

> 产出是「提纯版原文」——保留原意、论证链、案例与金句的干净稿，**不是摘要、也不是改写**。

## 特性

- **三种输入**：平台链接（抖音/小红书）、本地视频/音频、纯文字稿
- **自动化流水线**：视频提取 → 语音转文字(ASR) → 提纯去噪 → 结构化排版 → 交付飞书
- **提纯而非总结**：保留原意、论证链、案例、金句；去除口语填充词、ASR 同音错误、时间戳
- **自动交付飞书文档**（lark-doc），对话区只回链接不贴全文

## 适用场景

- 抖音/小红书爆款视频 → 提取文案做选题拆解
- 直播回放、播客、短视频 → 转逐字稿并提纯
- 已有文字稿/录音转写稿 → 直接整理成可分享原文

## 目录结构

```
.
├── SKILL.md                           # Skill 定义与完整操作规范
├── agents/
│   └── openai.yaml                    # OpenAI Agent 兼容配置
├── scripts/
│   ├── batch_asr_pipeline.py          # 本地视频批量 ASR 转写流水线
│   └── build_structured_transcript.py # 提纯稿 → 飞书文档构建
└── README.md
```

## 安装（Agent 视角）

本仓库为**扁平结构**（Skill 文件直接在根目录）。安装本质是把整个仓库复制到 Agent 的 skills 目录。

### 方式一：手动复制（推荐，最可靠）

```bash
# 1. 克隆
git clone https://github.com/duuhuang-ai/xhs-douyin-video-copy-purify.git /tmp/xhs-skill

# 2. 复制到 WorkBuddy skills 目录（目录名即 Skill 名，保持中文）
mkdir -p ~/.workbuddy/skills/小红书抖音视频文案提纯
cp -R /tmp/xhs-skill/. ~/.workbuddy/skills/小红书抖音视频文案提纯/

# 3. 重载 WorkBuddy 会话（或重启），Skill 即以新名字生效
```

> 其他 Agent 平台同理：把仓库内容放进对应 skills 目录，目录名用 `小红书抖音视频文案提纯`（与 SKILL.md 的 `name` 字段一致）。

### 方式二：`npx skills add` 类 CLI 的注意点

社区 `skills` CLI（`npx skills add <owner/repo>`）默认期望仓库内存在 `skills/<name>/SKILL.md` 布局，并会装到 `~/.agents/skills/` 再 symlink 到各 Agent 目录。本仓库是扁平结构，**不会被该类 CLI 自动识别**。若要用 CLI，需自行调整为 `skills/` 子目录布局，或安装后手动把目录复制到 `~/.workbuddy/skills/`（WorkBuddy 只读这个目录）。

## 配置前置依赖

Skill 通过环境变量读取凭证，**切勿硬编码**。

| 变量 | 用途 |
|---|---|
| `TIKHUB_API_KEY` | TikHub API，解析抖音/小红书分享链接、提取视频地址（国内 `api.tikhub.dev`，海外 `api.tikhub.io`） |
| `DASHSCOPE_API_KEY` | 阿里云百炼 DashScope，调用 Paraformer-v2 做 ASR 转写 |
| `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET` | 阿里云 OSS，上传本地视频换取稳定公开 URL |
| `OSS_BUCKET_NAME` | OSS 桶名（默认 `hermes-videos`） |
| `OSS_ENDPOINT` | OSS Endpoint（默认 `oss-cn-hangzhou.aliyuncs.com`） |

> **不需要百炼 Workspace ID**：本 Skill 直接用 DashScope SDK 调 Paraformer-v2，不走「应用 API」。

运行脚本的 Python 需安装：`oss2`、`dashscope`、`requests`、`imageio-ffmpeg`。

## 使用教程

详细图文教程见飞书 Wiki（上游权威文档）：
https://yulu-tech.feishu.cn/wiki/ART3wy2SEiwwGMkPT47cQSBMnlf

下面是基于 SKILL.md 的操作要点。

### 触发词

`视频文案提纯`、`小红书抖音视频文案提纯`、`文案提纯`、`整理文字稿`、`结构化逐字稿`、`直播文字稿`、`短视频文字稿`、`播客文字稿`、`录音转写稿`，或直接发送平台链接 / 本地视频。

### 模式 A：平台链接 → 视频 → ASR → 提纯

1. 用户发抖音（`v.douyin.com`、`douyin.com/video/...`）或小红书（`xiaohongshu.com/explore/...`、`xhslink.cn/`）分享链接。
2. 用 TikHub API 提取视频播放地址（CDN 链接短命，需立即下载）。
3. `curl` 下载视频（加 `Referer` 头破防盗链）。
4. 上传到 OSS 换取稳定公开 URL，再用百炼 Paraformer-v2 异步转写（支持中英文）。
5. 进入提纯（模式 C）。

### 模式 B：本地视频/音频 → OSS → ASR → 提纯

1. 校验本地文件（mp4/mov/avi/mkv/wav/mp3/flv/webm）。
2. 上传 OSS（桶设为公开读，或用 24h 签名 URL）。
3. Paraformer-v2 转写。
4. 多视频串行处理（百炼有 QPS 限制），全部转写后合并再提纯。

> 批量可用现成脚本：
> ```bash
> XHS_SOURCE_DIR="/path/to/videos" XHS_WORK_DIR="/tmp/xhs3" \
> OSS_ACCESS_KEY_ID=... OSS_ACCESS_KEY_SECRET=... OSS_BUCKET_NAME=... OSS_ENDPOINT=... \
> DASHSCOPE_API_KEY=... \
> PYTHON scripts/batch_asr_pipeline.py [rebuild]
> ```
> 其中 `PYTHON` 为已安装 `oss2`/`dashscope`/`requests`/`imageio-ffmpeg` 的 Python 解释器。脚本自动去重、`N.NN` 排序、超时加固、重试、per-video 容错。

### 模式 C：纯文字稿 → 提纯

直接对原始转写文本/文本文件应用提纯规则。

### 提纯规则要点

- **产出是「提纯版原文」，不是摘要、不是改写**：保留原意、语气、判断、案例、数字、类比、论证链与金句。
- 去除：时间戳、说话人标签、寒暄、废话、填充词、重复、ASR 噪点、直播噪音。
- 结构：`# 标题` → 少量 `##` 大主题（2–5 个）→ `###` 子标题 → 干净原文段落。
- 禁止章节：`一句话总结`、`核心要点`、`启发`、`结论`、`重点摘要` 等。
- 仅在高置信度下修正 ASR 同音词；不编造时间戳/说话人；不把全文加粗。

### 交付飞书文档

- 用 `lark-doc` Skill 创建飞书文档（标题同 `# 标题`），内容为正文 Markdown。
- 对话区**只回飞书文档链接 + 一行说明**（标题 + 字数 + 必要的 ASR 修正备注），不贴全文。

### 质量门禁（交付前自检）

- [ ] 来源行已附（模式 A：标题+原链接；模式 B：本地路径）
- [ ] 原意与论证顺序保留，非总结/清单/评论
- [ ] 寒暄/填充/重复/时间戳/说话人/碎片已去除
- [ ] 关键判断、案例、数字、原话保留
- [ ] 标题具体、限于真实主题
- [ ] 加粗克制（只标高价值内容）
- [ ] 飞书文档已创建（或已注明本地兜底）
- [ ] 对话回复仅一行（链接+标题+字数）

## 注意事项

### 网络路由

| 服务 | 网络路径 | 备注 |
|---|---|---|
| TikHub API | 需代理/VPN（Cloudflare，国内直连被挡） | Python `requests` 超时则用 `curl` 经 Bash |
| 阿里云 OSS | 直连（国内） | 脚本设 `NO_PROXY=*` 绕开代理 |
| 百炼 DashScope | 直连（国内） | 脚本设 `NO_PROXY=*` 绕开代理 |

### oss2 超时坑（实测）

`oss2.Bucket(...)` 不接收 `read_timeout` 参数（只认 `connect_timeout`），默认 60s 慢网会 `ReadTimeout`。正确做法：`oss2.Bucket(auth, endpoint, bucket, connect_timeout=120)` 后设 `bucket.timeout = 900`；上传/转写加 3 次重试 + 退避，主循环包 per-video try/except。

### ASR 同音词（常见修正）

小红书电商←小魔书店商、低粉←一份、爆款←报款；以及 AI→爱、Excel→excel 等英文识别错误。

## 相关链接

- 飞书使用教程（上游）：https://yulu-tech.feishu.cn/wiki/ART3wy2SEiwwGMkPT47cQSBMnlf
- 本 Skill 已从 `duuhuang-ai/dalu-skills` 独立迁出为单仓库。

## License

未指定许可证。如需用于生产，请自行评估或联系作者。
