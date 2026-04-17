# 微信插件补丁

## process-message.ts.patch

**目标路径：** `~/.openclaw/extensions/openclaw-weixin/src/messaging/process-message.ts`

**说明：**
这是 curiousbuddy skill 自动注入到微信插件的代码补丁（包含 aliyun-oss 和 c2e 功能）。
包含以下功能：

### Aliyun OSS 功能
1. 解题模式 / 批改模式 文字命令识别 + 模式切换
2. 模式下图片自动路由到 `aliyun_handler.py` 处理（上传 OSS + 调用 AI API）
3. 模式命令的自动回复（如"已进入解题模式，请发送图片~"）

### C2E 翻译功能
1. 翻译模式 / 解除模式 文字命令识别 + 模式切换
2. 翻译模式下文本自动路由到 `c2e_handler.py` 处理（Ollama 翻译 + Edge TTS）
3. 翻译模式下语音自动路由到 `c2e_handler.py`（Whisper 转录 + Ollama 翻译 + Edge TTS）
4. 翻译模式下图片回复警告"⚠️ 翻译模式仅支持文字和语音"

**使用方式：**
`python3 scripts/check_and_patch.py` 自动检测版本并打补丁（aliyun + c2e）。

**包含的改动：**
- 新增 module-level 变量：`_aliyunInterceptReply`、`_aliyunInterceptMode`、`_c2eInterceptReply`、`_c2eInterceptMode`
- 新增函数：`_aliyunModeCheck()`、`_c2eModeCheck()`
- 在 `processOneMessage()` 中新增：
  - 文字 body 提前提取（aliyun/c2e mode check + slash command）
  - C2E voice intercept（语音 → Whisper → 翻译 → TTS）
  - C2E text intercept（文本 → 翻译 → TTS）
  - C2E image warning
  - media download 提前（aliyun image intercept 需要）
  - aliyun/c2e reply intercept（模式命令回复）
  - aliyun image intercept（图片 AI 处理）

**兼容性：** 适用于 openclaw-weixin v2.1.8+
