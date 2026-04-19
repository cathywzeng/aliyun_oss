#!/usr/bin/env python3
"""
调用通义千问 AI 解题/批改 API
POST https://dashscope.aliyuncs.com/api/v1/apps/{app_id}/completion
"""

import json
import os
import sys
import urllib.request
import urllib.error


CONFIG_PATH = os.path.expanduser("~/.openclaw/memory/env_config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        return json.load(f)


def call_aliyun_api(image_urls: list, mode: str, config: dict = None) -> str:
    """调用通义千问 API，返回文本结果（LaTeX 格式）"""
    if config is None:
        config = load_config()

    app_id = config['dashscope_app_id']
    api_key = config['dashscope_api_key']

    url = f"https://dashscope.aliyuncs.com/api/v1/apps/{app_id}/completion"

    payload = {
        "input": {
            "prompt": mode,  # "解题模式" 或 "批改模式"
            "image_list": image_urls
        },
        "parameters": {}
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'X-DashScope-SSE': 'enable'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            # SSE 响应，需要逐行处理
            result_parts = []
            for line in resp:
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                # SSE 格式: data: {"..."}
                if line.startswith('data:'):
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                        # 根据不同事件类型处理
                        if data.get('event') == 'result':
                            choices = data.get('data', {}).get('choices', [{}])
                            for choice in choices:
                                for msg in choice.get('messages', []):
                                    content = msg.get('content', '')
                                    if content:
                                        result_parts.append(content)
                    except json.JSONDecodeError:
                        continue
            return ''.join(result_parts)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"API 调用失败 ({e.code}): {error_body}")
    except Exception as e:
        raise Exception(f"API 调用失败: {str(e)}")


def call_aliyun_api_simple(image_urls: list, mode: str, config: dict = None) -> str:
    """简化的 API 调用（非 SSE，直接解析 JSON 响应）"""
    if config is None:
        config = load_config()

    app_id = config['dashscope_app_id']
    api_key = config['dashscope_api_key']

    url = f"https://dashscope.aliyuncs.com/api/v1/apps/{app_id}/completion"

    payload = {
        "input": {
            "prompt": mode,
            "image_list": image_urls
        },
        "parameters": {}
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            output = data.get('output', {})
            # 兼容不同响应格式
            if isinstance(output, dict):
                text = output.get('text', '') or output.get('content', '')
            else:
                text = str(output)
            return text
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"API 调用失败 ({e.code}): {error_body}")
    except Exception as e:
        raise Exception(f"API 调用失败: {str(e)}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 call_api.py <image_url> <mode>")
        print("示例: python3 call_api.py 'https://...' '解题模式'")
        sys.exit(1)

    image_url = sys.argv[1]
    mode = sys.argv[2]

    try:
        result = call_aliyun_api_simple([image_url], mode)
        print(result)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
