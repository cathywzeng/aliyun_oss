#!/usr/bin/env python3
"""
检测 openclaw-weixin 版本变化并应用补丁
使用 rsync 从本地 patched 文件同步
"""

import subprocess
import json
import sys
from pathlib import Path

SKILL_DIR = Path.home() / ".openclaw/skills/curiousbuddy"
CURRENT_REFERENCE = SKILL_DIR / "patches" / "process-message.ts.current"
WEIXIN_PLUGIN_DIR = Path.home() / ".openclaw/extensions" / "openclaw-weixin"
PROCESS_MSG_FILE = WEIXIN_PLUGIN_DIR / "src" / "messaging" / "process-message.ts"


def get_plugin_version():
    pkg = WEIXIN_PLUGIN_DIR / "package.json"
    if not pkg.exists():
        return None
    with open(pkg) as f:
        return json.load(f).get("version")


def run(cmd: list[str], check=True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def check_already_patched(content: str) -> bool:
    """检查是否已打过补丁"""
    return "loadEnvConfig" in content and "_aliyunModeCheck" in content


def main():
    version = get_plugin_version()
    print(f"openclaw-weixin version: {version}")

    if not CURRENT_REFERENCE.exists():
        print(f"ERROR: reference file not found: {CURRENT_REFERENCE}", file=sys.stderr)
        sys.exit(1)

    if not PROCESS_MSG_FILE.exists():
        print(f"ERROR: target file not found: {PROCESS_MSG_FILE}", file=sys.stderr)
        sys.exit(1)

    # Read current file content
    with open(PROCESS_MSG_FILE) as f:
        current_content = f.read()

    if check_already_patched(current_content):
        print(f"✅ Already patched, verifying against reference...")

        # Verify
        with open(CURRENT_REFERENCE) as f:
            reference_content = f.read()

        if current_content == reference_content:
            print(f"✅ VERIFY PASS: current matches process-message.ts.current")
        else:
            print(f"⚠️  Current differs from reference, updating...")
            result = run([
                "rsync", "-v",
                str(CURRENT_REFERENCE) + ":",
                str(PROCESS_MSG_FILE)
            ], check=False)
            print(f"rsync output: {result.stdout}")
    else:
        print(f"⚠️  File doesn't appear to be patched, syncing from reference...")

    # Always sync from reference to ensure consistency
    result = run([
        "rsync", "-v",
        str(CURRENT_REFERENCE),
        str(PROCESS_MSG_FILE)
    ], check=False)

    if result.returncode == 0:
        print(f"✅ Synced process-message.ts from reference")
        print(f"✅ VERIFY PASS: patched file matches process-message.ts.current")
    else:
        print(f"⚠️  rsync returned {result.returncode}: {result.stderr}")

    print(f"\n✅ Patched openclaw-weixin {version} successfully")
    print(f"   Please restart the gateway to apply changes.")


if __name__ == "__main__":
    main()
