#!/usr/bin/env python3
import sys; sys.path.insert(0, '/home/admin/.openclaw/skills/aliyun-oss/scripts')

import json, os, time
MODE_FILE = os.path.expanduser("~/.openclaw/memory/weixin_mode.json")
with open(MODE_FILE, 'w') as f:
    json.dump({'mode': '解题模式'}, f)

from call_api import call_aliyun_api_simple
from latex_to_unicode import latex_to_plain_text

CONFIG_FILE = os.path.expanduser("~/.openclaw/memory/aliyun_config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# 测试几个不同的 URL 格式
URLS = [
    # 重新上传的深圳
    "https://<bucket-name>.oss-cn-shenzhen.aliyuncs.com/problem_uploads/1776057282_f06c46.jpg",
    # 原始 liteapp 公开 URL
    "https://bailian-datahub-data-share-prod.oss-cn-beijing.aliyuncs.com/runtime/temp/1994673641190580/15155479/301dc8d877c645e59efcada16f2543d0.1776053763798.jpg?Expires=1776312963&OSSAccessKeyId=***&Signature=***",
]

for url in URLS:
    print(f"\n{'='*60}")
    print(f"URL: {url[:80]}...")
    try:
        raw = call_aliyun_api_simple([url], "解题模式", config)
        print(f"SUCCESS ({len(raw)} chars):")
        print(raw[:400])
        print("\nUnicode:")
        print(latex_to_plain_text(raw))
        break
    except Exception as e:
        print(f"FAILED: {e}")
