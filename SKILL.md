---
name: curiousbuddy
description: 阿里云 OSS + 通义千问 API 集成技能，支持微信渠道的 AI 解题/批改和 C2E 中英翻译功能。
---

# curiousbuddy OpenClaw Skill

阿里云 OSS + 通义千问 API 技能（解题/批改）+ C2E 中英翻译。

## 功能概述

1. **OSS 上传** — 接收图片，上传到阿里云 OSS（<bucket-name>，深圳区域）
2. **API 调用** — 调用通义千问 AI 解题/批改 API
3. **LaTeX 转换** — 将 LaTeX 公式转换为 Unicode（微信可读）
4. **模式管理** — 支持"解题模式""批改模式"flag，通过 memory 持久化

## 核心脚本

| 脚本 | 功能 |
|------|------|
| `scripts/oss_uploader.py` | 上传图片到 OSS |
| `scripts/latex_to_unicode.py` | LaTeX → Unicode 转换 |
| `scripts/call_api.py` | 调用通义千问 API |
| `scripts/aliyun_handler.py` | 主处理器（编排以上三者） |
| `scripts/patch_weixin.py` | 为 openclaw-weixin 打补丁 |
| `scripts/check_and_patch.py` | 检测版本差异并打补丁 |

## 配置（敏感信息，写入 memory，不上传 Git）

```
OSS_BUCKET=<bucket-name>
OSS_REGION=cn-shenzhen
OSS_ACCESS_KEY=<你的AccessKey>
OSS_SECRET=<你的AccessKeySecret>
DASHSCOPE_API_KEY=<你的API Key>
DASHSCOPE_APP_ID=<你的App ID>
```

配置写入 `~/.openclaw/memory/aliyun_config.json`，此文件在 `.gitignore` 中，不会上传到 GitHub。

## 补丁管理

- 补丁目录：`~/.openclaw/skills/aliyun-oss/patches/`
- 补丁命名：`weixin-{plugin_version}.patch`
- 每次 Gateway 启动时自动检测是否需要打补丁
- 已打过的补丁记录在 `~/.openclaw/skills/aliyun-oss/patch_history.json`

## 使用方法

### 手动触发处理

```bash
python3 ~/.openclaw/skills/aliyun-oss/scripts/aliyun_handler.py \
  --image-url "https://..." \
  --mode "解题模式" \
  --output-channel weixin
```

### 检测并打补丁

```bash
python3 ~/.openclaw/skills/aliyun-oss/scripts/check_and_patch.py
```

## 注意事项

- 所有敏感信息（AK/SK/API Key）存储在 `~/.openclaw/memory/aliyun_config.json`，此文件在 `.gitignore` 中
- LaTeX 转换使用简单正则替换，支持常见数学符号
- 模式 flag 存储在 `~/.openclaw/memory/weixin_mode.json`
