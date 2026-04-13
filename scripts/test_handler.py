#!/usr/bin/env python3
"""测试 handler"""
import sys, json, os
sys.path.insert(0, '/home/admin/.openclaw/skills/aliyun-oss/scripts')

# Set mode
MODE_FILE = os.path.expanduser("~/.openclaw/memory/weixin_mode.json")
with open(MODE_FILE, 'w') as f:
    json.dump({'mode': '解题模式'}, f)
print("Mode: 解题模式")

from oss_uploader import upload_image_to_oss
from call_api import call_aliyun_api_simple
from latex_to_unicode import latex_to_plain_text

CONFIG_FILE = os.path.expanduser("~/.openclaw/memory/aliyun_config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# 用 liteapp 的公开 URL（腾讯云 URL，DashScope 可访问）
# sample 图片已经下载到本地，用本地路径上传测试
LOCAL_IMG = "/tmp/physics_sample.jpg"
print(f"Step 1: Uploading to OSS...")
try:
    oss_url = upload_image_to_oss(LOCAL_IMG, config)
    print(f"  OSS URL: {oss_url}")
    # NOTE: 如果 OSS bucket 不是公开的，DashScope 无法访问此 URL
    # 需要在阿里云控制台设置 bucket 策略允许公共读
except Exception as e:
    print(f"  OSS upload failed (bucket may not be public): {e}")
    oss_url = None

# 同时测试 liteapp 的原始公开 URL（应该能用）
SAMPLE_URL = "https://bailian-datahub-data-share-prod.oss-cn-beijing.aliyuncs.com/runtime/temp/1994673641190580/15155479/301dc8d877c645e59efcada16f2543d0.1776053763798.jpg?Expires=1776312963&OSSAccessKeyId=***&Signature=***"
print(f"\nStep 2: Calling AI API with liteapp URL...")
raw = call_aliyun_api_simple([SAMPLE_URL], "解题模式", config)
print(f"  Raw ({len(raw)} chars):")
print(raw[:500])
print("...")

print(f"\nStep 3: Converting LaTeX to Unicode...")
readable = latex_to_plain_text(raw)
print(f"\n=== 最终结果 ===")
print(readable)
