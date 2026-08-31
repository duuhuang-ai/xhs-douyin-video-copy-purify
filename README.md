# 小红书抖音视频文案提纯

把抖音 / 小红书视频链接、本地视频 / 音频、或原始文字稿，一键**提取 → 转写 → 提纯**成可直接分享的干净原文，并自动交付飞书文档。

> 产出是「**提纯版原文**」——保留原意、论证链、案例与金句的干净稿，**不是摘要、也不是改写**。

---

## Skill 概述

「小红书抖音视频文案提纯」是一个自动化流水线 Skill，能将抖音 / 小红书视频链接、本地视频文件或原始文字稿一键转化为结构清晰的「提纯版原文」，并自动交付到飞书文档。

**核心能力**：自动提取视频 → 语音转文字（ASR）→ 去除噪音 / 修正同音词 → 结构化排版 → 交付飞书文档。

---

## 适用场景

| 输入类型 | 举例 |
| --- | --- |
| 抖音 / 小红书分享链接 | `https://v.douyin.com/xxx/`、`https://xhslink.cn/xxx/` |
| 本地视频 / 音频文件 | `.mp4`、`.mov`、`.mkv`、`.mp3`、`.wav` 等 |
| 原始文字稿（纯文本） | 已有的直播逐字稿、播客文字稿、ASR 初稿 |

---

## 安装 Skill

将本仓库克隆到所用 Agent 的 skills 目录即可（目录名固定为 `小红书抖音视频文案提纯`，不可改名），克隆后重载 / 重启会话生效。

直接运行下面这条命令，会自动检测当前已安装的 Agent（WorkBuddy / Codex / Claude Code），并克隆到对应的 skills 目录，无需手动修改路径：

```bash
git clone https://github.com/duuhuang-ai/xhs-douyin-video-copy-purify.git \
  "$(for d in ~/.workbuddy/skills ~/.codex/skills ~/.claude/skills; do [ -d "$d" ] && { echo "$d"; break; }; done)/小红书抖音视频文案提纯"
```

> 本仓库为扁平结构（Skill 文件直接在根目录），克隆后整个目录即作为 Skill 目录直接使用，目录名必须保持中文 `小红书抖音视频文案提纯`，否则无法被识别。

---

## 依赖服务与注册

本 Skill 依赖四个服务，全部需要提前注册并获取凭证。

### TikHub —— 平台视频提取

作用：解析抖音 / 小红书分享链接，提取视频播放地址。

| 项目 | 说明 |
| --- | --- |
| 官网 | https://www.tikhub.io |
| 注册地址 | https://user.tikhub.io/register |
| API Key 获取 | 登录后进入用户控制台 → API 令牌 → 创建 API 令牌 |
| API 文档 | https://api.tikhub.io（Swagger） |
| 中文快速入门 | https://tikhub.io/zh/getting-started |
| API 域名（中国大陆） | `https://api.tikhub.dev` |
| API 域名（海外） | `https://api.tikhub.io` |

> 💡 注册后需验证邮箱才能使用 API。API Key 创建后仅显示一次，务必立即保存。大陆用户必须使用 `api.tikhub.dev` 域名（`api.tikhub.io` 被墙）。需要代理 / VPN 访问 TikHub API。付费端点需充值，支持 PayPal、支付宝、USDT。

### 阿里云百炼（DashScope）—— 语音转文字

作用：调用 Paraformer-v2 模型，将视频 / 音频转为文字。

| 项目 | 说明 |
| --- | --- |
| 百炼控制台 | https://bailian.aliyun.com |
| DashScope 控制台 | https://dashscope.aliyun.com |
| API Key 管理页 | https://dashscope.aliyuncs.com/console/apiKey |
| 模型名称 | `paraformer-v2` |

获取 API Key 步骤：

1. 登录[阿里云百炼控制台](https://bailian.aliyun.com)，阅读并同意服务协议（首次使用会自动开通）。
2. 进入 [API Key 管理页](https://dashscope.aliyuncs.com/console/apiKey)。
3. 点击「创建 API Key」，选择归属账号与默认业务空间，点击确定。
4. 复制生成的 API Key（格式：`sk-xxxxxxxxxxxxxxxx`），仅显示一次，务必妥善保存。
5. 新用户可领取超 7000 万 tokens 的 90 天免费额度。

> 💡 本 Skill 直接调用 DashScope SDK 的 Paraformer-v2 模型，**不需要百炼的「业务空间 ID」（Workspace ID）**。业务空间 ID 仅在使用百炼应用编排、智能体、工作流时才需要。

### 阿里云 OSS（对象存储）—— 视频中转存储

作用：Paraformer-v2 需要可公网访问的视频 URL，本地视频或平台提取的视频（CDN 链接有有效期）需先上传到 OSS 获得稳定公网地址。

| 项目 | 说明 |
| --- | --- |
| OSS 产品页 | https://www.aliyun.com/product/oss |
| OSS 控制台 | https://oss.console.aliyun.com |
| AccessKey 管理 | https://ram.console.aliyun.com/manage/ak |

**第一步：开通 OSS 服务**

1. 访问 [OSS 产品页](https://www.aliyun.com/product/oss)，点击「立即开通」。
2. 新用户可免费试用 3 个月。

**第二步：创建 Bucket**

1. 进入 [OSS 控制台](https://oss.console.aliyun.com) → Bucket 列表 → 创建 Bucket。
2. 配置参数：

| 参数 | 推荐值 | 说明 |
| --- | --- | --- |
| Bucket 名称 | 自定义（如 `hermes-videos`） | 全局唯一，仅小写字母 / 数字 / 短横线，3–63 字符 |
| 地域 | 华东 2（上海）或华北 2（北京） | 选择离你最近的 |
| 存储类型 | 标准存储 | 临时存储，性价比最高 |
| 读写权限 | 公共读 | 必须设为公共读，否则 Paraformer 无法访问 |

3. 创建后，如果默认开启了「阻止公共访问」，需要在 Bucket 设置中关闭，然后把读写权限改为「公共读」。

**第三步：获取 AccessKey**

1. 进入 [RAM 访问控制 → 用户](https://ram.console.aliyun.com/users)，创建子账号（推荐，不建议用主账号 AK）。
2. 为子账号授予 `AliyunOSSFullAccess` 权限。
3. 创建 AccessKey，保存 AccessKey ID 和 AccessKey Secret。

### 飞书 CLI（lark-cli）—— 文档交付

作用：在流水线最后一步创建飞书云文档，将提纯后的文字稿交付为可读、可分享的飞书文档。

为什么需要：整个 Skill 的交付环节不走本地文件，而是直接写入飞书。SKILL.md 明确要求通过 `lark-doc` 创建飞书文档，底层依赖 lark-cli 命令行工具。

**在 WorkBuddy 内使用**

如果你的飞书连接器（Connector）已连接，lark-cli 预装于 WorkBuddy 的 Node.js 环境中，无需任何额外安装。Skill 触发时自动可用。

验证方式：

```bash
lark-cli auth status --verify
# 应输出 verified: true 和你的飞书用户名
```

**WorkBuddy 外独立复现**

如果你脱离 WorkBuddy、在终端中手动跑这套流水线，需要安装并配置 lark-cli：

1. **安装**（环境要求 Node.js 16+，含 npm / npx）：
   ```bash
   npm install -g @larksuite/cli
   lark-cli --version
   ```
2. **配置应用凭证**（仅需一次）：
   ```bash
   lark-cli config init --new --brand feishu --lang zh
   ```
   执行后终端会输出一个飞书授权链接，在浏览器中打开并按提示完成应用创建和授权。
3. **登录授权**：
   ```bash
   lark-cli auth login --recommend
   ```
   `--recommend` 自动选择日历、消息、文档、多维表格、通讯录等常用权限，省去逐项选择。
4. **验证**：
   ```bash
   lark-cli auth status --verify
   ```
   看到 `verified: true` 和自己的飞书用户名即表示成功。

| 参考文档 | 链接 |
| --- | --- |
| 飞书 CLI 安装指南（开放平台） | https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md |
| Feishu CLI 中文文档站 | https://feishu-cli.com/zh/feishu-cli-installation-guide.html |
| lark-cli GitHub 仓库 | https://github.com/larksuite/cli |

---

## 环境变量配置

将以下环境变量写入你的 shell 配置文件（`~/.zshrc` 或 `~/.bashrc`）：

```bash
# TikHub（平台视频提取）
export TIKHUB_API_KEY="你的TikHub API Key"

# 阿里云百炼 / DashScope（语音转文字）
export DASHSCOPE_API_KEY="sk-你的DashScope API Key"

# 阿里云 OSS（视频中转存储）
export OSS_ACCESS_KEY_ID="你的AccessKey ID"
export OSS_ACCESS_KEY_SECRET="你的AccessKey Secret"
export OSS_BUCKET_NAME="hermes-videos"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
```

> 💡 `OSS_ENDPOINT` 根据你 Bucket 所在的地域填写。常见地域 Endpoint：
> - 华东 2（上海）：`oss-cn-shanghai.aliyuncs.com`
> - 华北 2（北京）：`oss-cn-beijing.aliyuncs.com`
> - 华南 1（深圳）：`oss-cn-shenzhen.aliyuncs.com`

配置后执行 `source ~/.zshrc` 使其生效。可通过 `echo $TIKHUB_API_KEY` 验证。

---

## 三种输入模式详解

### 模式 A：平台链接 → 视频提取 → 语音转写 → 提纯

适用场景：你有一个抖音或小红书分享链接，想提取视频并整理成文字稿。

**完整流程**

1. 用户发送链接
2. TikHub API 解析分享链接，提取视频 URL 和标题
3. 下载视频到本地临时目录（`/tmp/structured_transcript/`）
4. 上传视频到 OSS，获取公网可访问的 URL
5. 调用百炼 Paraformer-v2 进行语音转文字
6. 对 ASR 原始文本执行提纯规则（去噪音、修正同音词、结构化排版）
7. 通过 lark-cli 创建飞书文档，输出链接

**关键接口**

- 抖音：`GET https://api.tikhub.dev/api/v1/douyin/app/v3/fetch_one_video_by_share_url?share_url={URL_ENCODED}`
- 小红书：`GET https://api.tikhub.dev/api/v1/xiaohongshu/app_v2/get_video_note_detail?share_text={URL_ENCODED}`

**网络路由注意事项**

| 操作 | 是否需要代理 | 说明 |
| --- | --- | --- |
| 调用 TikHub API | 需要代理 / VPN | TikHub 服务在 Cloudflare 后，大陆直连不通 |
| 下载视频 | 可直连 | 视频 CDN 在国内，但要加 `Referer: https://www.douyin.com` 防盗链头 |
| 上传 OSS | 直连 | 国内服务，建议设置 `NO_PROXY=*` 跳过代理 |
| 调用 DashScope | 直连 | 国内服务，建议设置 `NO_PROXY=*` 跳过代理 |

### 模式 B：本地视频 → OSS 上传 → 语音转写 → 提纯

适用场景：你本地有录制的视频、音频文件（如会议录像、播客录音），想转写成结构化文字稿。

**完整流程**

1. 用户提供本地文件路径（支持批量）
2. 验证文件存在且格式受支持：`mp4, mov, avi, mkv, wav, mp3, flv, webm`
3. 上传每个文件到 OSS（路径：`transcripts/文件名`），设置公开读或生成 24 小时签名 URL
4. 调用百炼 Paraformer-v2 转写
5. 如果多个文件，逐个处理（百炼有 QPS 限制），全部完成后合并为一个文档
6. 提纯 → 通过 lark-cli 交付飞书文档

### 模式 C：原始文字稿 → 直接提纯

适用场景：你已经有一段原始的文字稿（直播逐字稿、播客文字稿、ASR 初稿），需要去除噪音、修正错误、结构化排版。

**完整流程**

1. 用户提供原始文本（直接粘贴或 `.txt` 文件）
2. 执行提纯规则：
   - **去除**：时间戳、说话人标签、寒暄、废话、重复、残句
   - **修正**：高置信度 ASR 同音词错误
   - **保留**：原意、语气、关键判断、案例、数字、类比、金句
3. 结构化排版：
   - 一个 `h1` 标题（从视频标题 / 主题 / 来源名衍生）
   - 少量 `h2` 大主题（通常 2–5 个）
   - 具体的 `h3` 小标题
   - 清洗后的原风格段落
4. 通过 lark-cli 交付飞书文档

**提纯规则要点**

- 禁止出现以下章节：`一句话总结`、`核心要点`、`启发`、`结论`、`重点摘要`、`补充内容`。
- 不添加原文没有的事实、外部信息或个人解读。
- 不将内容改写成新文章——读起来应该还是说话人的语气。
- 仅在关键判断、强引述、具体原则处使用加粗，不为每个段落加粗。

**常见 ASR 同音词修正**

| 错误识别 | 应为 |
| --- | --- |
| 小魔书店商 | 小红书电商 |
| 一份 | 低粉（如「一份爆款」应为「低粉爆款」） |
| 报款 | 爆款 |
| 爱（AI 语境） | AI |
| Cloud code / Clod Code | Claude Code |
| notebookrm | NotebookLM |

---

## 输出与交付

所有提纯后的文档都通过飞书文档交付。完成后在聊天中仅输出：

1. 飞书文档链接（可点击）
2. 一行摘要：已交付飞书文档——《标题》，约 N 字

不会将完整文字稿直接输出到聊天窗口。

---

## 故障排查

### TikHub API 调用失败

- 确认 API Key 是否正确（格式：Bearer 后跟 key）。
- 大陆用户是否使用了 `api.tikhub.dev`（不是 `.io`）。
- 是否通过代理 / VPN 访问。
- 账户是否已验证邮箱，是否有可用余额。

### DashScope 转写失败

- 确认 `DASHSCOPE_API_KEY` 格式为 `sk-` 开头。
- 视频 URL 是否可公网访问（OSS Bucket 权限是否为公共读）。
- 视频格式是否受支持（Paraformer-v2 支持常见音视频格式）。
- 视频时长是否过长（建议单文件不超过 4 小时）。

### OSS 上传失败

- 确认 `OSS_ACCESS_KEY_ID` 和 `OSS_ACCESS_KEY_SECRET` 正确。
- 确认 `OSS_ENDPOINT` 与 Bucket 所在地域匹配。
- 确认子账号已授权 `AliyunOSSFullAccess`。
- 如走代理导致超时，Python 脚本中需设置 `NO_PROXY=*` 绕过代理。

### 视频 CDN 链接过期

TikHub 提取的视频 CDN 链接有效期很短（可能几分钟即失效）。提取后应立即下载，不要间隔太久再下载。

### lark-cli 创建飞书文档失败

- 确认 lark-cli 已安装：`lark-cli --version`
- 确认已登录授权：`lark-cli auth status --verify`
- 如报权限不足，尝试重新登录授权：`lark-cli auth login --recommend`

---

## 完整配置检查清单

开始使用前，逐项确认：

- [ ] TikHub 账号已注册并验证邮箱
- [ ] TikHub API Key 已创建并写入环境变量 `TIKHUB_API_KEY`
- [ ] 阿里云百炼（DashScope）已开通
- [ ] DashScope API Key 已创建并写入环境变量 `DASHSCOPE_API_KEY`
- [ ] 阿里云 OSS 已开通
- [ ] OSS Bucket 已创建，读写权限为「公共读」
- [ ] OSS AccessKey（ID + Secret）已创建并写入环境变量
- [ ] OSS Bucket 名称和 Endpoint 已写入环境变量
- [ ] 所有环境变量已 `source` 生效
- [ ] lark-cli 已安装（WorkBuddy 用户可跳过）
- [ ] lark-cli 已登录授权（`lark-cli auth status --verify` 返回 `verified: true`）
- [ ] 代理 / VPN 可用（用于 TikHub API 调用）
- [ ] 本地 Python 环境已安装 `dashscope`、`oss2` 两个包

---

## 关键平台链接汇总

| 平台 | 链接 | 用途 |
| --- | --- | --- |
| TikHub 官网 | https://www.tikhub.io | 了解产品 |
| TikHub 注册 | https://user.tikhub.io/register | 注册账号 |
| TikHub 用户控制台 | https://user.tikhub.io/dashboard/api | 管理 API Key |
| TikHub API 文档 | https://api.tikhub.io | 接口参考（Swagger） |
| TikHub 中文入门 | https://tikhub.io/zh/getting-started | 快速入门指南 |
| 阿里云百炼控制台 | https://bailian.aliyun.com | 百炼主控制台 |
| DashScope 控制台 | https://dashscope.aliyun.com | 模型服务管理 |
| 百炼 API Key 管理 | https://dashscope.aliyuncs.com/console/apiKey | 创建 / 管理 API Key |
| 阿里云 OSS 产品页 | https://www.aliyun.com/product/oss | 开通 OSS |
| 阿里云 OSS 控制台 | https://oss.console.aliyun.com | 管理 Bucket |
| 阿里云 RAM 控制台 | https://ram.console.aliyun.com | 管理 AccessKey 和权限 |
| 飞书 CLI 安装指南 | https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md | lark-cli 官方安装文档 |
| Feishu CLI 中文文档站 | https://feishu-cli.com/zh/feishu-cli-installation-guide.html | 中文安装教程 |
| lark-cli GitHub | https://github.com/larksuite/cli | 开源仓库 |

---

## License

未指定许可证。如需用于生产，请自行评估或联系作者。
