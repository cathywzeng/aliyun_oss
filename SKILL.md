---
name: curiousbuddy
description: 阿里云 OSS + 通义千问 API 集成技能，支持微信渠道的 AI 解题/批改和 C2E 中英翻译功能。
---

# curiousbuddy OpenClaw Skill

阿里云 OSS + 通义千问 API 技能（解题/批改）+ C2E 中英翻译。

## 功能概述

1. **AI 解题模式** — 拍照上传题目，AI 返回完整解答
2. **批改模式** — 拍照上传作业，AI 返回批改结果
3. **解题思路模式** — 拍照上传题目，AI 返回考点分析和方法点拨（不给最终答案）
4. **C2E 翻译模式** — 中文文本/语音实时翻译为英文 + 语音合成
5. **OSS 上传** — 图片自动上传到阿里云 OSS
6. **LaTeX 转换** — 将 LaTeX 公式转换为 Unicode

## 核心脚本

| 脚本 | 功能 |
|------|------|
| `scripts/aliyun_handler.py` | 阿里云解题/批改处理器 |
| `scripts/c2e_handler.py` | C2E 翻译模式处理器 |
| `scripts/oss_uploader.py` | OSS 上传工具 |
| `scripts/call_api.py` | 通义千问 API 调用 |
| `scripts/latex_to_unicode.py` | LaTeX → Unicode 转换 |
| `scripts/check_and_patch.py` | 检测版本差异并打补丁 |
| `scripts/test_c2e_handler.py` | C2E 功能测试 |

## 首次配置

### 1. 配置文件

在 `~/.openclaw/memory/env_config.json` 中填入实际值：

```json
{
  "oss_bucket": "<bucket-name>",
  "oss_region": "cn-shenzhen",
  "oss_access_key": "<YOUR_AK>",
  "oss_secret": "<YOUR_SK>",
  "dashscope_api_key": "<YOUR_API_KEY>",
  "dashscope_app_id": "<YOUR_APP_ID>",
  "MINIMAX_API_KEY": "<YOUR_MINIMAX_KEY>",
  "MINIMAX_BASE_URL": "https://api.minimaxi.com/anthropic",
  "EDGE_TTS_MODULE_PATH": "/opt/homebrew/lib/node_modules/node-edge-tts",
  "EDGE_TTS_SCRIPT": "~/.openclaw/skills/curiousbuddy/c2e/tts-converter.js",
  "NODE_BIN": "/opt/homebrew/bin/node",
  "OLLAMA_MODEL": "qwen2.5:7b-instruct",
  "OLLAMA_BIN": "ollama",
  "WHISPER_BIN": "",
  "FASTER_WHISPER_MODEL": "tiny",
  "TMP_DIR": "/tmp/c2e-wechat"
}
```

> 敏感信息（AK/SK/API Key）存储在 `memory/` 目录，不上传 Git。

### 2. 运行一键安装（如有）

```bash
bash ~/.openclaw/skills/curiousbuddy/setup.sh
```

### 3. 安装依赖

```bash
# Python
pip install openai requests

# Node.js global
npm install -g node-edge-tts
```

## 补丁管理

openclaw-weixin 升级后，重新运行：

```bash
python3 ~/.openclaw/skills/curiousbuddy/scripts/check_and_patch.py
```

## 使用方法

### 解题/批改/解题思路模式

- 发送 `解题模式` / `批改模式` / `解题思路` → 进入对应模式
- 发送图片 → AI 处理并返回结果
- 发送 `解除模式` → 清除模式

### C2E 翻译模式

- 发送 `翻译模式` 或 `c2e` → 进入翻译模式
- 发送中文文本 → 返回英文翻译 + 英文语音
- 发送中文语音 → Whisper 转录 → 英文翻译 + 英文语音
- 发送 `解除模式` → 清除翻译模式

## 目录结构

```
curiousbuddy/
├── SKILL.md                   # Skill 定义文件
├── setup.sh                   # 一键安装脚本
├── env_config.json            # 配置文件模板
├── scripts/
│   ├── aliyun_handler.py      # 阿里云解题/批改处理器
│   ├── c2e_handler.py         # C2E 翻译模式处理器
│   ├── oss_uploader.py        # OSS 上传工具
│   ├── call_api.py            # 通义千问 API 调用
│   ├── latex_to_unicode.py    # LaTeX 转 Unicode
│   ├── check_and_patch.py     # 补丁管理
│   └── test_c2e_handler.py    # C2E 测试脚本
├── c2e/
│   ├── tts-converter.js       # Edge TTS 转换脚本
│   └── package.json           # Node.js 依赖
└── patches/
    ├── process-message.ts.original  # 原始干净文件
    ├── process-message.ts.current  # 已打补丁文件
    └── process-message.ts.patch    # 补丁文件
```
