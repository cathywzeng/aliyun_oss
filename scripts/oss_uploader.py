#!/usr/bin/env python3
"""
阿里云 OSS 上传工具
将图片上传到 <bucket-name>，返回签名 URL（默认6小时有效期）
支持两种方式：
1. 从 OSS URL 下载（oss2 签名）
2. 从公网 URL 下载（urllib）
3. 从本地文件上传
"""

import json
import os
import sys
import time
import uuid
import tempfile
import urllib.request
import urllib.error
from urllib.parse import urlparse

try:
    import oss2
except ImportError:
    print("ERROR: oss2 not installed. Run: pip install oss2")
    sys.exit(1)


CONFIG_PATH = os.path.expanduser("~/.openclaw/memory/env_config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}，请先配置阿里云密钥")
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_bucket(config: dict = None):
    if config is None:
        config = load_config()
    auth = oss2.Auth(config['oss_access_key'], config['oss_secret'])
    bucket = oss2.Bucket(
        auth,
        f"https://oss-{config['oss_region']}.aliyuncs.com",
        config['oss_bucket']
    )
    return bucket


def upload_local_to_oss(local_path: str, config: dict = None, sign_expires_seconds: int = 21600) -> str:
    """
    上传本地文件到 OSS，返回带签名的 URL（默认6小时有效期）
    sign_expires_seconds: 签名有效期，默认6小时
    """
    if config is None:
        config = load_config()

    bucket = get_bucket(config)

    ext = os.path.splitext(local_path)[1] or '.jpg'
    timestamp = int(time.time())
    rand = uuid.uuid4().hex[:6]
    filename = f"ai-homework-helper/uploads/solver/{timestamp}_{rand}{ext}"

    with open(local_path, 'rb') as f:
        bucket.put_object(filename, f.read())

    # 返回直链（bucket 是 public-read，无需签名；签名 URL 会将 / 编码为 %2F，DashScope 无法访问）
    region = config['oss_region']
    bucket_name = config['oss_bucket']
    direct_url = f"https://{bucket_name}.oss-{region}.aliyuncs.com/{filename}"
    return direct_url


def upload_image_to_oss(image_url: str, config: dict = None, sign_expires_seconds: int = 21600) -> str:
    """
    上传图片到 OSS，返回带签名的 URL
    自动识别图片来源：
    - oss:// 开头的 OSS 对象路径 -> 直接上传
    - http/https 开头的 URL -> 下载后上传
    - 本地路径 -> 直接上传
    """
    if config is None:
        config = load_config()

    bucket = get_bucket(config)
    tmpfile = None

    try:
        if not image_url.startswith('http'):
            # 本地文件
            return upload_local_to_oss(image_url, config, sign_expires_seconds)

        # 判断是否是 OSS URL（需要 oss2 处理签名下载）
        parsed = urlparse(image_url)
        is_oss = '.oss-' in parsed.netloc and 'aliyuncs.com' in parsed.netloc

        if is_oss:
            # 从 OSS 下载（自动处理签名）
            bucket_name = parsed.netloc.split('.')[0]
            object_key = parsed.path.lstrip('/')
            ext = os.path.splitext(object_key)[1] or '.jpg'
        else:
            # 公网 URL，下载
            ext = os.path.splitext(parsed.path)[1] or '.jpg'

        # 下载到临时文件
        tmpfile = tempfile.mktemp(suffix=ext)
        if is_oss:
            bucket.get_object_to_file(object_key, tmpfile)
        else:
            req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(tmpfile, 'wb') as f:
                    f.write(resp.read())

        # 上传并返回签名 URL
        return upload_local_to_oss(tmpfile, config, sign_expires_seconds)

    finally:
        if tmpfile and os.path.exists(tmpfile):
            try:
                os.remove(tmpfile)
            except:
                pass


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 oss_uploader.py <image_url_or_local_path>")
        sys.exit(1)

    image_url = sys.argv[1]
    try:
        result = upload_image_to_oss(image_url)
        print(result)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
