#!/usr/bin/env python3
"""
阿里云 AI 解题意处理器
整合 OSS 上传 + API 调用 + LaTeX 转换
支持两种图片来源：
1. 直接使用原始 URL（如果 DashScope 可访问）
2. 上传到 OSS（如果原始 URL 不可达）
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from latex_to_unicode import latex_to_unicode, latex_to_plain_text

CONFIG_PATH = os.path.expanduser("~/.openclaw/memory/aliyun_config.json")
MODE_PATH = os.path.expanduser("~/.openclaw/memory/weixin_mode.json")


def load_config():
    path = os.path.expanduser(CONFIG_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path) as f:
        return json.load(f)


def load_mode():
    path = os.path.expanduser(MODE_PATH)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f).get('mode')


def save_mode(mode):
    path = os.path.expanduser(MODE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump({'mode': mode}, f, ensure_ascii=False)


def clear_mode():
    path = os.path.expanduser(MODE_PATH)
    if os.path.exists(path):
        os.remove(path)


def is_url_accessible(url: str, timeout: int = 5) -> bool:
    """检查 URL 是否可访问（用于判断 DashScope 是否能访问）"""
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except:
        return False


def process_image(image_url: str, output: str = 'text') -> str:
    """
    处理图片：
    1. 尝试直接用原始 URL（如果可访问）
    2. 上传到 OSS（用于持久化）
    3. 调用通义千问 API
    4. 转换 LaTeX 为 Unicode
    5. 返回结果
    """
    from oss_uploader import upload_image_to_oss
    from call_api import call_aliyun_api_simple

    config = load_config()
    mode = load_mode()

    if not mode:
        raise ValueError("未设置模式，请先发送'解题模式'或'批改模式'")

    # Step 1: 尝试直接用原始 URL
    use_direct = False
    print(f"[DEBUG] Testing direct URL access: {image_url[:80]}...", file=sys.stderr)
    if image_url.startswith('http') and is_url_accessible(image_url, timeout=5):
        print(f"[DEBUG] Direct URL accessible, using it directly", file=sys.stderr)
        use_direct = True
        api_image_url = image_url
    else:
        # Step 2: 上传到 OSS
        print(f"[DEBUG] Uploading to OSS...", file=sys.stderr)
        try:
            api_image_url = upload_image_to_oss(image_url, config)
            print(f"[DEBUG] Uploaded to OSS: {api_image_url}", file=sys.stderr)
        except Exception as e:
            print(f"[DEBUG] OSS upload failed: {e}, using direct URL", file=sys.stderr)
            # 最后手段：直接用原始 URL（即使可能不可达）
            api_image_url = image_url

    # Step 3: 调用 API
    print(f"[DEBUG] Calling API with mode={mode}...", file=sys.stderr)
    result = call_aliyun_api_simple([api_image_url], mode, config)
    print(f"[DEBUG] API returned {len(result)} chars", file=sys.stderr)

    # Step 4: 转换 LaTeX（Unicode 模式，保留公式结构）
    readable = latex_to_unicode(result)

    if output == 'json':
        return json.dumps({
            'api_image_url': api_image_url,
            'used_direct': use_direct,
            'raw': result,
            'readable': readable
        }, ensure_ascii=False, indent=2)

    return readable


def handle_text_input(text: str) -> str:
    """处理文本输入：设置/清除模式"""
    text = text.strip()

    if text in ('解题模式', '批改模式'):
        save_mode(text)
        return f"已进入{text}，请发送图片~"
    elif text in ('解除模式', '清空模式'):
        old_mode = load_mode()
        clear_mode()
        return f"已解除{old_mode or '当前模式'}，模式已清空"
    else:
        return None  # 不处理


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='阿里云 AI 解题处理器')
    parser.add_argument('--image-url', help='图片 URL 或本地路径')
    parser.add_argument('--text', help='文本输入（设置模式）')
    parser.add_argument('--output', default='text', choices=['text', 'json'], help='输出格式')
    args = parser.parse_args()

    try:
        if args.text:
            result = handle_text_input(args.text)
            if result:
                print(result)
            else:
                print("未识别的命令")
        elif args.image_url:
            result = process_image(args.image_url, args.output)
            print(result)
        else:
            parser.print_help()
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
