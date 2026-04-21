# curiousbuddy OpenClaw Skill

阿里云 OSS + 通义千问 API 集成，用于 OpenClaw 微信渠道的 AI 解题/批改功能，以及 TRSL 中英翻译功能。

## 功能

- 🤖 **AI 解题模式** — 拍照上传题目，AI 返回完整解答
- ✏️ **批改模式** — 拍照上传作业，AI 返回批改结果
- 💡 **解题思路模式** — 发送题目文字，AI 返回考点分析和方法点拨（不给最终答案）
- 🌐 **翻译模式** — 中文文本/语音实时翻译为英文 + 语音合成
- 📤 **OSS 自动上传** — 图片自动上传到阿里云 OSS
- 📝 **LaTeX → Unicode** — 公式转换为微信可读格式

## 目录结构

```
curiousbuddy/
├── SKILL.md              # Skill 定义文件
├── scripts/
│   ├── aliyun_handler.py # 阿里云解题/批改处理器
│   ├── trsl_handler.py     # TRSL 翻译模式处理器
│   ├── oss_uploader.py    # OSS 上传工具
│   ├── call_api.py        # 通义千问 API 调用
│   ├── latex_to_unicode.py # LaTeX 转 Unicode
│   └── test_trsl_handler.py # TRSL 测试脚本
├── patches/              # 补丁文件（按版本）
└── memory/               # 配置和模式（不提交）
```

## 首次配置

### 1. 配置文件

将以下内容写入 `~/.openclaw/memory/env_config.json`（**不要提交到 Git**，敏感信息用占位符）：

```json
{
  "oss_bucket": "<bucket-name>",
  "oss_region": "cn-shenzhen",
  "oss_access_key": "YOUR_AK",
  "oss_secret": "YOUR_SK",
  "dashscope_api_key": "YOUR_API_KEY",
  "dashscope_app_id": "YOUR_APP_ID",
  "MINIMAX_API_KEY": "YOUR_MINIMAX_KEY",
  "MINIMAX_BASE_URL": "https://api.minimaxi.com/anthropic",
  "EDGE_TTS_MODULE_PATH": "/opt/homebrew/lib/node_modules/node-edge-tts",
  "EDGE_TTS_SCRIPT": "~/.openclaw/skills/curiousbuddy/trsl/tts-converter.js",
  "NODE_BIN": "/opt/homebrew/bin/node",
  "OLLAMA_MODEL": "qwen2.5:7b-instruct",
  "OLLAMA_BIN": "ollama",
  "WHISPER_BIN": "",
  "FASTER_WHISPER_MODEL": "tiny",
  "TMP_DIR": "/tmp/trsl-wechat"
}
```

> **注意**：TRSL 翻译功能相关配置（如不使用可留空）：
> - `MINIMAX_API_KEY` / `MINIMAX_BASE_URL` — MiniMax API 翻译
> - `EDGE_TTS_MODULE_PATH` — Node.js 全局 node-edge-tts 模块路径
> - `EDGE_TTS_SCRIPT` — Edge TTS 转换脚本路径
> - `NODE_BIN` — Node.js 可执行文件路径
> - `OLLAMA_MODEL` / `OLLAMA_BIN` — 本地 Ollama 备选模型
> - `WHISPER_BIN` / `FASTER_WHISPER_MODEL` — Whisper 语音识别
> - `TMP_DIR` — 临时文件目录

如使用旧版 `aliyun_config.json`，功能不受影响（会 fallback 读取）。

### 2. 运行补丁：
```bash
python3 ~/.openclaw/skills/curiousbuddy/scripts/check_and_patch.py
```

> `check_and_patch.py` 会自动备份原文件为 `.original`，应用 `process-message.ts.patch`，并验证与 `process-message.ts.current` 是否一致。

## 使用方法

### 解题/批改模式

- 发送 `解题模式` → 进入解题模式
- 发送 `批改模式` → 进入批改模式
- 发送图片 → AI 处理并返回结果
- 发送 `解除模式` → 清除模式

### 解题思路模式

- 发送 `解题思路` → 进入解题思路模式
- 发送题目图片 → AI 返回考点分析和方法点拨（不给最终答案）
- 与解题模式、批改模式共用阿里云拦截通道
- 发送 `解除模式` → 清除模式

### 翻译模式（TRSL）

- 发送 `翻译模式` 或 `trsl` → 进入翻译模式
- 发送中文文本 → 返回英文翻译 + 英文语音
- 发送中文语音 → Whisper 转录 → 英文翻译 + 英文语音
- 发送图片 → 回复警告"⚠️ 翻译模式仅支持文字和语音"
- 发送 `解除模式` 或 `trsl-exit` → 清除翻译模式

## 补丁管理

openclaw-weixin 升级后，运行：

```bash
python3 ~/.openclaw/skills/curiousbuddy/scripts/check_and_patch.py
```

脚本会自动：
1. 备份原文件为 `.original`（仅首次）
2. 从 `.original` 恢复到干净状态
3. 应用 `process-message.ts.patch`
4. 验证与 `process-message.ts.current` 一致

补丁文件位于 `~/.openclaw/skills/curiousbuddy/patches/`。

## 安全说明

- 所有敏感信息（AK/SK/API Key）存储在 `memory/` 目录，不上传 Git
- `.gitignore` 已排除所有 `memory/` 下的文件
