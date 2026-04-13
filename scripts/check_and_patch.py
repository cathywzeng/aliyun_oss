#!/usr/bin/env python3
"""
检测 openclaw-weixin 版本变化并自动打补丁
每次插件升级后，自动注入 aliyun handler 逻辑
"""

import subprocess
import os
import sys
import json
import re
import shutil
from pathlib import Path

SKILL_DIR = Path.home() / ".openclaw/skills/aliyun-oss"
PATCH_DIR = SKILL_DIR / "patches"
PATCH_HISTORY = SKILL_DIR / "patch_history.json"
HANDLER_MODULE = SKILL_DIR / "scripts" / "aliyun_handler.py"
WEIXIN_PLUGIN_DIR = Path.home() / ".openclaw/extensions" / "openclaw-weixin"
PROCESS_MSG_FILE = WEIXIN_PLUGIN_DIR / "src" / "messaging" / "process-message.ts"


def get_plugin_version():
    pkg = WEIXIN_PLUGIN_DIR / "package.json"
    if not pkg.exists():
        return None
    with open(pkg) as f:
        return json.load(f).get("version")


def load_history():
    if PATCH_HISTORY.exists():
        with open(PATCH_HISTORY) as f:
            return json.load(f)
    return {"patches": {}, "last_check": None}


def save_history(history):
    PATCH_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with open(PATCH_HISTORY, "w") as f:
        json.dump(history, f, indent=2)


def read_file(path):
    with open(path) as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def backup_file(path):
    backup = Path(str(path) + ".bak")
    shutil.copy2(path, backup)
    return backup


def check_already_patched(content: str) -> bool:
    """检查是否已打过补丁"""
    return "aliyun_handler" in content or "_ALIYUN_MODE_CHECK" in content


def inject_handler_code() -> str:
    """生成要注入的 handler 代码（TypeScript 片段）"""
    return """
// === ALIYUN HANDLER PATCH START ===
// 这段代码由 aliyun-oss skill 自动注入，请勿手动修改

async function _aliyunCheckMode(
  textBody: string,
  accountId: string,
): Promise<{ mode: string | null; intercept: boolean }> {
  const SKILL_DIR = os.homedir() + "/.openclaw/skills/aliyun-oss";
  const MODE_FILE = os.homedir() + "/.openclaw/memory/weixin_mode.json";
  const FS = await import("node:fs/promises");

  try {
    const modeData = JSON.parse(await FS.readFile(MODE_FILE, "utf-8"));
    const mode = modeData?.mode ?? null;
    if (!mode) return { mode: null, intercept: false };

    const { execSync } = await import("node:child_process");
    // 检查是否是模式命令
    if (textBody === "解题模式" || textBody === "批改模式") {
      // 更新模式
      await FS.writeFile(MODE_FILE, JSON.stringify({ mode: textBody }), "utf-8");
      return { mode: textBody, intercept: true, reply: `已进入${textBody}，请发送图片~` };
    }
    if (textBody === "解除模式" || textBody === "清空模式") {
      if (mode) {
        await FS.writeFile(MODE_FILE, JSON.stringify({ mode: null }), "utf-8");
        return { mode: null, intercept: true, reply: `已解除${mode}，模式已清空` };
      }
      return { mode: null, intercept: true, reply: "当前无模式，已清空" };
    }
    return { mode, intercept: false };
  } catch {
    return { mode: null, intercept: false };
  }
}
// === ALIYUN HANDLER PATCH END ===
"""


def inject_process_imports(content: str) -> str:
    """确保导入了必要的模块"""
    if "os.homedir" not in content:
        content = content.replace(
            "import path from \"node:path\";",
            'import path from "node:path";\nimport os from "node:os";'
        )
    return content


def inject_mode_check(content: str) -> str:
    """在 processOneMessage 开头注入模式检查逻辑"""
    # 在 extractTextBody 之前注入我们的检查
    marker = "// === ALIYUN HANDLER PATCH START ==="
    if marker in content:
        return content  # 已打过补丁

    # 在函数开始处插入代码
    # 找到 extractTextBody 函数，在它之前插入
    injection = """
// === ALIYUN HANDLER PATCH START ===
// aliyun-oss skill auto-injected
let _aliyunInterceptReply: string | null = null;
let _aliyunInterceptMode: string | null = null;

async function _aliyunModeCheck(
  textBody: string,
): Promise<{ intercept: boolean; reply?: string }> {
  const MODE_FILE = os.homedir() + "/.openclaw/memory/weixin_mode.json";
  try {
    const { readFile, writeFile } = await import("node:fs/promises");
    let modeData: { mode: string | null } = { mode: null };
    try {
      const raw = await readFile(MODE_FILE, "utf-8");
      modeData = JSON.parse(raw);
    } catch { /* no mode file */ }

    const mode = modeData?.mode;
    if (textBody === "解题模式" || textBody === "批改模式") {
      await writeFile(MODE_FILE, JSON.stringify({ mode: textBody }), "utf-8");
      _aliyunInterceptReply = `已进入${textBody}，请发送图片~`;
      return { intercept: true };
    }
    if (textBody === "解除模式" || textBody === "清空模式") {
      const prev = mode;
      await writeFile(MODE_FILE, JSON.stringify({ mode: null }), "utf-8");
      _aliyunInterceptReply = prev ? `已解除${prev}，模式已清空` : "当前无模式，已清空";
      return { intercept: true };
    }
    _aliyunInterceptMode = mode ?? null;
    return { intercept: false };
  } catch {
    return { intercept: false };
  }
}
// === ALIYUN HANDLER PATCH END ===
"""
    # 在 import path 之后插入
    content = content.replace(
        'import path from "node:path";',
        'import path from "node:path";\nimport os from "node:os";'
    )
    # 在 extractTextBody 函数定义之前插入
    content = content.replace(
        "/** Extract text body from item_list",
        injection + "\n/** Extract text body from item_list"
    )
    return content


def inject_image_intercept(content: str) -> str:
    """在图片处理后、AI dispatch 之前注入拦截逻辑"""
    marker = "_ALIYUN_IMAGE_INTERCEPT"
    if marker in content:
        return content

    # 找到 ctx = weixinMessageToMsgContext 这行，在其后、authorization 检查之前
    # 注入图片拦截逻辑
    inject = """
  // === ALIYUN IMAGE INTERCEPT START ===
  // aliyun-oss skill: check if we need to route to aliyun API
  const _aliyunMediaOpts = mediaOpts;
  if (_aliyunMediaOpts?.mediaUrl && _aliyunInterceptMode) {
    try {
      const { execSync } = await import("node:child_process");
      const scriptPath = os.homedir() + "/.openclaw/skills/aliyun-oss/scripts/aliyun_handler.py";
      const result = execSync(
        `python3 "${scriptPath}" --image-url "${_aliyunMediaOpts.mediaUrl}" --output json`,
        { timeout: 120, encoding: "utf-8", maxBuffer: 10 * 1024 * 1024 }
      );
      const parsed = JSON.parse(result);
      // Send the readable result back via weixin
      const replyText = parsed.readable || parsed.raw || "处理完成";
      await sendMessageWeixin({
        to: ctx.To,
        text: replyText,
        opts: { baseUrl: deps.baseUrl, token: deps.token, contextToken },
      });
      logger.info("[aliyun] image intercepted and handled, reply sent");
      return; // Skip normal AI pipeline
    } catch (err) {
      logger.error(`[aliyun] intercept error: ${String(err)}, falling through to AI`);
    }
  }
  // === ALIYUN IMAGE INTERCEPT END ===
"""
    # 在 "const ctx = weixinMessageToMsgContext" 之后、"const rawBody" 之前插入
    content = content.replace(
        "  const ctx = weixinMessageToMsgContext(full, deps.accountId, mediaOpts);\n\n  // --- Framework command authorization ---",
        "  const ctx = weixinMessageToMsgContext(full, deps.accountId, mediaOpts);\n" + inject + "\n  // --- Framework command authorization ---"
    )

    return content


def inject_reply_intercept(content: str) -> str:
    """注入模式命令的回复拦截（textBody 检查后立即处理）"""
    marker = "_ALIYUN_REPLY_INTERCEPT"
    if marker in content:
        return content

    # 在 slash command 处理之后、media download 之前插入
    # 找到 "const textBody = extractTextBody(full.item_list);" 这行之后
    # 检查是否有 _aliyunInterceptReply 需要先发送
    inject = """
  // === ALIYUN REPLY INTERCEPT START ===
  // 如果是模式命令回复，直接发送并返回
  if (_aliyunInterceptReply) {
    const replyText = _aliyunInterceptReply;
    _aliyunInterceptReply = null;
    try {
      await sendMessageWeixin({
        to: ctx.To,
        text: replyText,
        opts: { baseUrl: deps.baseUrl, token: deps.token, contextToken: getContextTokenFromMsgContext(ctx) },
      });
    } catch (e) { deps.errLog(`aliyun reply intercept error: ${String(e)}`); }
    return;
  }
  // === ALIYUN REPLY INTERCEPT END ===
"""
    content = content.replace(
        "  if (mediaItem) {\n    const label = refMediaItem ? \"ref\" : \"inbound\";",
        "  // === ALIYUN REPLY CHECK ===\n" + inject + "  if (mediaItem) {\n    const label = refMediaItem ? \"ref\" : \"inband\";"
    )

    return content


def do_patch(content: str) -> str:
    """对 process-message.ts 打补丁"""
    content = inject_mode_check(content)
    content = inject_image_intercept(content)
    content = inject_reply_intercept(content)
    return content


def create_patch_file(current_version: str, original: str, patched: str):
    """将补丁保存为 patch 文件"""
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    patch_file = PATCH_DIR / f"weixin-{current_version}.patch"

    import difflib
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        patched.splitlines(keepends=True),
        fromfile=f"process-message.ts (original {current_version})",
        tofile=f"process-message.ts (patched)"
    )
    with open(patch_file, "w") as f:
        f.write("# unified diff patch\n")
        f.write(f"# Target: openclaw-weixin {current_version}\n")
        f.write("# Generated by aliyun-oss skill\n\n")
        f.writelines(diff)

    return patch_file


def patch():
    """执行补丁逻辑"""
    if not PROCESS_MSG_FILE.exists():
        print(f"ERROR: {PROCESS_MSG_FILE} not found", file=sys.stderr)
        sys.exit(1)

    current_version = get_plugin_version()
    history = load_history()

    # 检查是否已经打过这个版本的补丁
    if history["patches"].get(current_version, {}).get("applied"):
        print(f"Plugin version {current_version} already patched, skipping.")
        return

    # 读取当前文件
    original_content = read_file(PROCESS_MSG_FILE)

    if check_already_patched(original_content):
        print("Already patched, recording in history.")
        history["patches"][current_version] = {
            "applied": True,
            "already_patched": True,
            "at": str(Path(__file__).resolve())
        }
        save_history(history)
        return

    # 备份原文件
    backup = backup_file(PROCESS_MSG_FILE)
    print(f"Backed up original to {backup}")

    # 打补丁
    patched_content = do_patch(original_content)

    # 验证语法（简单检查）
    if patched_content == original_content:
        print("WARNING: patching produced no changes!", file=sys.stderr)

    # 保存补丁后的文件
    write_file(PROCESS_MSG_FILE, patched_content)

    # 保存 patch 文件
    patch_file = create_patch_file(current_version, original_content, patched_content)

    # 更新历史
    history["patches"][current_version] = {
        "applied": True,
        "at": str(Path(__file__).resolve()),
        "patch_file": str(patch_file)
    }
    history["last_check"] = str(Path(__file__).resolve())
    save_history(history)

    print(f"✅ Patched openclaw-weixin {current_version}")
    print(f"   Patch saved to: {patch_file}")
    print(f"   Backup saved to: {backup}")
    print("   Please restart the gateway to apply changes.")


if __name__ == "__main__":
    patch()
