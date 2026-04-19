#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/aliyun-oss/scripts"))

import json, os
MODE_FILE = os.path.expanduser("~/.openclaw/memory/weixin_mode.json")
with open(MODE_FILE, 'w') as f:
    json.dump({'mode': '解题模式'}, f)

from call_api import call_aliyun_api_simple
from latex_to_unicode import latex_to_plain_text

CONFIG_FILE = os.path.expanduser("~/.openclaw/memory/env_config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# 用刚上传到 OSS 的公开图片 URL（刚才 Step 1 的结果）
OSS_URL = "https://<bucket-name>.oss-cn-shenzhen.aliyuncs.com/problem_uploads/1776057178_42c41d.jpg"

print(f"Image: {OSS_URL}")
print(f"Calling AI API...")
raw = call_aliyun_api_simple([OSS_URL], "解题模式", config)
print(f"Raw ({len(raw)} chars):")
print(raw[:800])
print("\n---\n")
readable = latex_to_plain_text(raw)
print("Unicode result:")
print(readable)
