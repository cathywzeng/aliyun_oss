# aliyun-oss OpenClaw Skill

阿里云 OSS + 通义千问 API 集成，用于 OpenClaw 微信渠道的 AI 解题/批改功能。

## 功能

- 🤖 **AI 解题模式** — 拍照上传题目，AI 返回 LaTeX 解答
- ✏️ **批改模式** — 拍照上传作业，AI 返回批改结果
- 📤 **OSS 自动上传** — 图片自动上传到阿里云 OSS
- 📝 **LaTeX → Unicode** — 公式转换为微信可读格式

## 目录结构

```
aliyun-oss/
├── SKILL.md              # Skill 定义文件
├── scripts/
│   ├── aliyun_handler.py # 主处理器
│   ├── oss_uploader.py   # OSS 上传工具
│   ├── call_api.py       # 通义千问 API 调用
│   ├── latex_to_unicode.py # LaTeX 转 Unicode
│   └── check_and_patch.py # 插件补丁管理
├── patches/              # 补丁文件（按版本）
└── memory/               # 配置和模式（不提交）
```

## 首次配置

1. 将以下内容写入 `~/.openclaw/memory/aliyun_config.json`（**不要提交到 Git**）：

```json
{
  "oss_bucket": "<bucket-name>",
  "oss_region": "cn-shenzhen",
  "oss_access_key": "YOUR_AK",
  "oss_secret": "YOUR_SK",
  "dashscope_api_key": "YOUR_API_KEY",
  "dashscope_app_id": "YOUR_APP_ID"
}
```

2. 运行补丁：
```bash
python3 ~/.openclaw/skills/aliyun-oss/scripts/check_and_patch.py
```

## 使用方法

- 发送 `解题模式` → 进入解题模式
- 发送 `批改模式` → 进入批改模式
- 发送图片 → AI 处理并返回结果
- 发送 `解除模式` → 清除模式

## 补丁管理

每次 `openclaw-weixin` 升级后，运行：

```bash
python3 ~/.openclaw/skills/aliyun-oss/scripts/check_and_patch.py
```

补丁历史记录在 `~/.openclaw/skills/aliyun-oss/patch_history.json`。

## 安全说明

- 所有敏感信息（AK/SK/API Key）存储在 `memory/` 目录，不上传 Git
- `.gitignore` 已排除所有 `memory/` 下的文件
