#!/usr/bin/env python3
"""完整流程测试：上传 -> 签名URL -> DashScope API -> LaTeX转换"""
import sys
sys.path.insert(0, '/home/admin/.openclaw/skills/aliyun-oss/scripts')
import json
import os

from oss_uploader import upload_image_to_oss
from call_api import call_aliyun_api_simple
from latex_to_unicode import latex_to_plain_text

config_path = os.path.expanduser("~/.openclaw/memory/aliyun_config.json")
mode_path = os.path.expanduser("~/.openclaw/memory/weixin_mode.json")

with open(mode_path, 'w') as f:
    json.dump({'mode': '解题模式'}, f)

with open(config_path) as f:
    config = json.load(f)

LOCAL = "/tmp/physics_sample.jpg"
print("Step 1: Uploading to OSS (signed URL)...")
signed_url = upload_image_to_oss(LOCAL, config)
print(f"  Signed URL: {signed_url[:100]}...")

print("Step 2: Calling DashScope API...")
raw = call_aliyun_api_simple([signed_url], "解题模式", config)
print(f"  Raw ({len(raw)} chars): {raw[:300]}...")

print("Step 3: Converting LaTeX...")
result = latex_to_plain_text(raw)
print("\n=== 最终结果 ===")
print(result)
