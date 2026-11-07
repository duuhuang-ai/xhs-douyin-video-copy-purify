# 小红书抖音视频文案提纯

把视频或音频中的讲话整理成可阅读、可分享的**提纯版原文**。你可以提供小红书、抖音或视频号视频链接、本地视频或音频，或者已有的文字稿。Skill 会根据输入选择提取、转写、整理和交付的步骤。

它整理的是原作者的表达：保留观点、案例、数字和论证过程，去除明显的口头重复、寒暄和转写噪音。结果不是摘要，也不是重新创作的文章。默认交付飞书文档；也可以在请求中指定其他交付方式。

> 视频号链接处理为**实验性功能**：已完成离线解密对照，尚未使用真实视频号链接、TikHub、OSS 和百炼完成端到端验收。服务或平台变化可能导致失败；已有的本地视频、音频或文字稿也可直接处理。

## 可以处理什么

| 输入 | 处理方式 | 需要的服务 |
| --- | --- | --- |
| 小红书、抖音、视频号视频分享链接 | 提取视频、转写，再整理原文 | TikHub、阿里云 OSS、百炼语音识别；飞书文档用于默认交付 |
| 本地视频或音频 | 上传媒体、转写，再整理原文 | 阿里云 OSS、百炼语音识别；飞书文档用于默认交付 |
| 已有文字稿 | 直接整理内容，无须语音识别 | 只有创建飞书文档时需要飞书连接 |
| 飞书妙记导出的文字记录文档 | 读取已有文字并整理 | 需要可用的飞书文档读取和创建能力 |

视频文件和音频文件常见格式包括 MP4、MOV、MKV、MP3 和 WAV。批量示例脚本目前只扫描指定文件夹顶层的 **MP4**，其他格式需由 Agent 根据实际情况处理，不能假定该脚本支持全部格式。视频中有音乐、多人同时说话或专有名词时，转写可能出错，请核对重要内容。

## 开始使用

### 1. 安装 Skill

你可以把这个仓库链接发给支持安装 Skill 的 Agent，让它安装并说明安装结果：

```text
请安装这个 Skill：https://github.com/duuhuang-ai/xhs-douyin-video-copy-purify
```

也可以用 Git 手动安装。仓库根目录本身就是 Skill 目录，需要包含 `SKILL.md`、`agents/` 和 `scripts/`。以下示例会创建目录；如果目标已存在，先备份并核对已有内容，不要直接覆盖：

**Codex（macOS / Linux）**

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/duuhuang-ai/xhs-douyin-video-copy-purify.git ~/.codex/skills/小红书抖音视频文案提纯
```

如果配置了 `CODEX_HOME`，请将目标改为该目录下的 `skills/小红书抖音视频文案提纯`。Windows 用户可在 Git Bash 中使用上面的命令，或让 Agent 按自己的 Codex skills 路径安装。重启或重新打开会话后检查是否识别，具体发现机制以当前客户端配置为准。

**WorkBuddy**

将仓库克隆到 WorkBuddy 当前使用的 skills 目录，目录名使用 `小红书抖音视频文案提纯`。不同安装和工作区的目录可能不同，可让 WorkBuddy 先检查并安装到它实际使用的位置，然后重新加载会话。本仓库未验证所有 WorkBuddy 版本的安装路径。

### 2. 按输入配置服务

**只整理文字稿**不需要 TikHub、OSS 或百炼。若需要默认交付飞书文档，先确保 Agent 可以用当前用户身份访问并创建飞书文档；例如配置可用的 `lark-cli`。如果飞书不可用，可以要求先输出本地草稿。

处理视频或音频时，除网络与可用的 Python 环境外，按用途准备：

| 服务或工具 | 用途 | 何时需要 |
| --- | --- | --- |
| [TikHub](https://www.tikhub.io/) | 获取小红书或抖音视频信息 | 平台分享链接 |
| [阿里云 OSS](https://www.aliyun.com/product/oss) | 暂存音视频，供语音识别服务读取 | 视频或音频转写 |
| [阿里云百炼 / DashScope](https://bailian.console.aliyun.com/) | Paraformer-v2 语音识别 | 视频或音频转写 |
| 飞书文档及可用的客户端工具 | 读取飞书文字记录或创建结果文档 | 使用飞书作为来源或交付位置 |
| Python、`oss2`、`dashscope`、`requests`、`imageio-ffmpeg` | 运行批量 MP4 脚本 | 使用仓库提供的批量脚本 |

这些外部服务可能收费，具体价格、可用地区和接口限制以服务商为准。分享链接可能失效或受平台限制。请只处理有权使用的内容；音视频会上传至你配置的云存储并提交语音识别服务，使用前确认适合上传。

在受管理的 Python 虚拟环境中安装批量脚本的 Python 依赖，例如：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install oss2 dashscope requests imageio-ffmpeg
```

Windows PowerShell 的激活命令为 `.\.venv\Scripts\Activate.ps1`。示例在当前目录创建 `.venv`，请先选择合适的工作目录；仓库未锁定依赖版本，安装结果受环境和服务更新影响。

### 3. 配置凭证

按需在当前终端环境中设置，下面均为**占位符**；不要把真实密钥写入公开仓库、聊天记录或截图。下面以 macOS / Linux shell 为例，其他系统按对应方式设置环境变量：

```bash
export TIKHUB_API_KEY="替换为你的 TikHub Key"          # 仅平台链接需要
export DASHSCOPE_API_KEY="替换为你的百炼 Key"         # 转写需要
export OSS_ACCESS_KEY_ID="替换为你的 OSS AccessKey ID"
export OSS_ACCESS_KEY_SECRET="替换为你的 OSS AccessKey Secret"
export OSS_BUCKET_NAME="替换为你的存储桶名称"
export OSS_ENDPOINT="替换为你的 OSS endpoint"
```

OSS 存储桶、地区和访问权限由使用者自行配置。脚本使用 24 小时有效的签名 URL，视频或音频会留在 OSS 中；不要为图方便把存储桶设为公开读取。相关流量、存储和转写可能产生费用。结束后的云端对象与本地中间文件，应由使用者确认后按自己的保留政策处理。

### 4. 向 Agent 发起任务

提供链接：

```text
使用小红书抖音视频文案提纯 Skill，整理这条视频的讲话内容，保留原意和案例，生成飞书文档：<视频分享链接>
```

提供本地文件：

```text
使用这个 Skill 整理本地视频 <文件路径>，先转写再提纯，生成飞书文档。
```

已有文字稿：

```text
使用这个 Skill 整理以下文字稿，保留观点、数字和案例，只清理口头重复：<文字稿>
```

飞书妙记导出的文字记录可以提供文档链接；Agent 需要对该文档有读取权限。默认结果包含来源、按内容组织的标题和整理后的原文。短视频的开头、节奏和关键表述应尽量保留；不确定的专有名词需要人工核对。

## 视频号链接：如何使用

向已安装此 Skill 的 Agent 直接提供你有权处理的视频号分享链接：

```text
使用小红书抖音视频文案提纯 Skill，整理这条视频号的讲话，保留原意和案例，并生成飞书文档：<视频号分享链接>
```

Agent 应检查 TikHub、OSS、百炼及飞书是否可用。视频会经 TikHub 获取、下载和解密，随后上传你配置的 OSS 并提交百炼转写，最后整理为原文。提供文字稿时不需要这些转写服务。由于该链路尚未做真实端到端验收，首次使用建议选择一段短视频，并核对解密后视频是否可播放、文字是否完整。

也可以在安装好依赖、设置好上文凭证后，让 Agent 执行下面的命令；`<Skill目录>`、链接和工作目录均需替换。工作目录必须是**尚不存在**的路径，脚本会创建它：

```bash
python "<Skill目录>/scripts/wechat_channels_extract.py" "<视频号分享链接>" --work-dir "<本次全新工作目录>"
```

可选设置 `TIKHUB_API_BASE` 以指定 TikHub 服务地址；未设置时使用 `https://api.tikhub.dev`。网络连通性、接口权限和费用以服务商实际情况为准。

成功后目录内有加密下载文件 `encrypted.mp4`、解密文件 `decrypted.mp4`、原始转写 `raw.txt` 和来源信息 `meta.json`。Agent 还要读取并提纯 `raw.txt`，再按你的要求交付。脚本使用随机 OSS 对象名称，并保留云端对象及本地中间文件；失败时也可能留下部分文件。脚本只做基础 MP4 标识检查，**不等于完整播放验证**。请勿分享解密密钥、媒体临时地址或 OSS 签名地址。

如果链接接口或解密失败，可提供已合法取得的本地视频、音频或文字稿继续处理。视频号解密使用 MIT 许可的独立 Python 实现，来源和许可见仓库 `scripts/ISAAC64-LICENSE.txt` 与下方说明。

## 批量处理本地 MP4

`scripts/batch_asr_pipeline.py` 是可选工具：它会按顺序抽取音频、上传 OSS、调用百炼，并保存原始转写。Agent 仍需阅读和提纯转写内容，脚本本身不会自动生成完成版飞书文档。

下面的命令要求先激活安装好依赖的 Python 环境，并设置上面的 OSS 和百炼凭证：

```bash
export XHS_SOURCE_DIR="/替换为/MP4文件夹"
export XHS_WORK_DIR="/替换为/本次全新工作目录"
export XHS_OSS_PREFIX="transcripts/替换为本次唯一标识"
python "<Skill目录>/scripts/batch_asr_pipeline.py"
```

- 每一批使用全新的工作目录和唯一 OSS 前缀。脚本可能复用旧清单及旧转写；前缀相同会覆盖对应的 OSS 对象。
- 脚本只扫描顶层 `.mp4` 文件，并按特定文件名规则去重和排序。运行后先核对 `manifest.json` 的实际路径与本次文件一致；不适合该命名规则时，先让 Agent 检查并调整。
- 输出包括 `manifest.json`、`audio/`、`raw/` 和 `pipeline.log`。这些文件及 OSS 对象会保留；不要仅凭完成日志判断成功，应检查失败记录和实际转写。
- 大文件、长录音、网络波动和服务限流可能导致失败或额外费用；可先用单个短文件验证。

## 常见问题

**为什么识别不到 Skill？** 检查安装目录下是否直接有 `SKILL.md`，而不是多套了一层目录；确认安装到了当前 Agent 实际使用的 skills 目录，然后重新打开会话。不同产品的加载方式可能不同。

**为什么链接提取失败？** 检查分享链接是否有效、TikHub 凭证和对应接口是否可用，以及网络是否能访问该服务。平台和第三方接口可能变化，不能保证所有视频均可提取。

**为什么转写失败？** 检查百炼、OSS 的凭证与服务权限，文件是否上传成功，签名 URL 是否能在有效期内供识别服务读取，以及文件格式和服务额度。避免把包含签名的地址或凭证发到公开场所。

**可以只整理文字、不上传视频吗？** 可以。直接提供文字稿即可，不需要 TikHub、OSS 或语音识别。飞书不可用时可指定本地交付。

**视频号链接无法处理怎么办？** 这是尚未做真实端到端验收的实验性功能。请先检查 TikHub 访问、链接及接口权限，核对错误阶段；也可以提供已有的本地音视频或文字稿。

**整理结果会完全准确吗？** 不能保证。自动转写和整理可能误识别名字、数字、语气和上下文，发表或用于重要决策前请对照原始内容核对。

## 仓库内容与许可

- `SKILL.md`：Agent 使用的流程、整理规则与注意事项。
- `scripts/batch_asr_pipeline.py`：批量 MP4 音频提取、上传和转写。
- `scripts/wechat_channels_extract.py`：实验性视频号提取、解密和转写。
- `scripts/isaac64.py`：视频号解密使用的第三方实现，来源为 [wechat-channels-downloader-skill](https://github.com/junlytech-ship-it/wechat-channels-downloader-skill/tree/ef8d292b9e94b1f1753785080b5dda4ef079ca4c)，许可见 `scripts/ISAAC64-LICENSE.txt`。
- `scripts/build_structured_transcript.py`：根据已有文字稿生成 Markdown 结构草稿；自动替换结果仍需人工核对。
- `agents/openai.yaml`：Codex 的展示信息。
- `LICENSE`：本仓库自身的许可条款；外部服务与第三方材料遵循其各自条款。
