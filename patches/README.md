# 微信插件补丁

## process-message.ts.patch

**目标路径：** `~/.openclaw/extensions/openclaw-weixin/src/messaging/process-message.ts`

**说明：**
这是 aliyun-oss skill 自动注入到微信插件的代码补丁。
包含以下功能：
1. 解题模式 / 批改模式 文字命令识别 + 模式切换
2. 模式下图片自动路由到 `aliyun_handler.py` 处理（上传 OSS + 调用 AI API）
3. 模式命令的自动回复（如"已进入解题模式，请发送图片~"）

**使用方式：**
直接覆盖到目标路径（插件已通过 skill 的 `check_and_patch.py` 自动打补丁，无需手动操作）。

**包含的改动：**
- 新增 module-level 变量：`_aliyunInterceptReply`、`_aliyunInterceptMode`
- 新增函数：`_aliyunModeCheck()`
- 在 `processOneMessage()` 中新增：
  - 文字 body 提前提取（aliyun mode check + slash command）
  - media download 提前（aliyun image intercept 需要）
  - aliyun reply intercept（模式命令回复）
  - aliyun image intercept（图片 AI 处理）

**兼容性：** 适用于 openclaw-weixin v2.1.8
