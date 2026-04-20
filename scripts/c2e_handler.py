#!/usr/bin/env python3
"""
C2E (Chinese→English) 翻译模式处理器
整合 Ollama 翻译 + Edge TTS 语音合成 + Whisper 语音识别
用于微信渠道的实时翻译模式
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, Union

import requests

# Config file path (env_config.json — used because Node.js execFile does not
# pass parent-process env vars to the child; credentials must be read from file)
CONFIG_PATH = "~/.openclaw/memory/env_config.json"

def load_env_config():
    """Load config from env_config.json."""
    path = os.path.expanduser(CONFIG_PATH)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def get_env_or_config(key: str, default: str = "") -> str:
    """Get value from env var first, then env_config.json. Expands ~ in paths."""
    val = os.environ.get(key, "")
    if val:
        return os.path.expanduser(val)
    cfg = load_env_config()
    return os.path.expanduser(cfg.get(key, default))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Mode file path (shared with aliyun-oss)
MODE_PATH = os.environ.get("MODE_PATH", "~/.openclaw/memory/weixin_mode.json")

# Config file path (for backward compatibility with existing deployments)
CONFIG_PATH = "~/.openclaw/memory/env_config.json"

# MiniMax Anthropic-compatible API (for translation)
# Credentials: set ANTHROPIC_AUTH_TOKEN and ANTHROPIC_BASE_URL env vars.
# For backward compatibility, falls back to MINIMAX_API_KEY / MINIMAX_BASE_URL.
# ANTHROPIC_AUTH_TOKEN is set by the OpenClaw gateway; fall back to
# MINIMAX_API_KEY in env_config.json for direct-script usage.
MINIMAX_API_KEY = os.environ.get("ANTHROPIC_AUTH_TOKEN") or get_env_or_config("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")

OLLAMA_MODEL = get_env_or_config("OLLAMA_MODEL", "qwen2.5:7b-instruct")
OLLAMA_BIN = get_env_or_config("OLLAMA_BIN", "ollama")
WHISPER_BIN = get_env_or_config("WHISPER_BIN", "")
FASTER_WHISPER_MODEL = get_env_or_config("FASTER_WHISPER_MODEL", "tiny")
NODE_BIN = get_env_or_config("NODE_BIN", "node")
EDGE_TTS_SCRIPT = get_env_or_config(
    "EDGE_TTS_SCRIPT",
    str(Path(__file__).parent.parent / "c2e" / "tts-converter.js")
)
EDGE_TTS_MODULE_PATH = get_env_or_config("EDGE_TTS_MODULE_PATH", "")
TMP_DIR = Path(get_env_or_config("TMP_DIR", "/tmp/c2e-wechat"))
TMP_DIR.mkdir(parents=True, exist_ok=True)


def load_c2e_mode():
    """读取 c2e 模式状态（与 aliyun_oss 共享 weixin_mode.json）"""
    path = os.path.expanduser(MODE_PATH)
    if not os.path.exists(path):
        return None
    try:
        data = json.load(open(path))
        return data.get("c2e", None)
    except (json.JSONDecodeError, IOError):
        return None


def save_c2e_mode(mode):
    """保存 c2e 模式（保留 aliyun 模式）"""
    path = os.path.expanduser(MODE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = {}
    if os.path.exists(path):
        try:
            existing = json.load(open(path))
        except (json.JSONDecodeError, IOError):
            pass
    existing["c2e"] = mode
    with open(path, "w") as f:
        json.dump(existing, f, ensure_ascii=False)


def clear_c2e_mode():
    """清除 c2e 模式（保留 aliyun 模式）"""
    path = os.path.expanduser(MODE_PATH)
    if not os.path.exists(path):
        return
    try:
        data = json.load(open(path))
        data.pop("c2e", None)
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False)
    except (json.JSONDecodeError, IOError):
        pass



def run_cmd(cmd: list[str], timeout: int = 120, env: Optional[dict] = None) -> str:
    """执行命令并返回 stdout"""
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"command failed: {' '.join(cmd)}")
    return p.stdout.strip()


def clean_ollama(text: str) -> str:
    """清理 ANSI 控制字符"""
    text = re.sub(r"\x1B\[[0-9;?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    return text.strip()


def translate_zh_to_en(chinese: str) -> str:
    """使用 MiniMax API（若已配置）或 Ollama（默认）将中文翻译为英文。"""
    if MINIMAX_API_KEY and MINIMAX_BASE_URL:
        try:
            resp = requests.post(
                f"{MINIMAX_BASE_URL}/v1/messages",
                headers={
                    "x-api-key": MINIMAX_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "MiniMax-M2.7",
                    "max_tokens": 1024,
                    "temperature": 0.3,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Translate the following Chinese to English. "
                                "Keep names, numbers, dates, and IDs exact. "
                                "Do not add facts. Output only English text in natural style.\n\n"
                                f"Chinese:\n{chinese}"
                            ),
                        }
                    ],
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if block.get("type") == "text":
                        return block["text"].strip()
            return str(content)
        except requests.Timeout:
            raise RuntimeError("[c2e] MiniMax API timed out after 10s")
        except Exception as e:
            raise RuntimeError(f"[c2e] MiniMax API error: {e}")

    if not OLLAMA_MODEL:
        raise RuntimeError(
            "[c2e] No translation backend configured. "
            "Set ANTHROPIC_AUTH_TOKEN (or MINIMAX_API_KEY) or OLLAMA_MODEL env var."
        )

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": f"Translate the following Chinese to English. Keep names, numbers, dates, and IDs exact. Do not add facts. Output only English text in natural style.\n\nChinese:\n{chinese}",
                "stream": False,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
    except Exception as e:
        raise RuntimeError(f"[c2e] Ollama API error: {e}")



def tts_edge(text: str, out_mp3: Path) -> Optional[Path]:
    """使用 Edge TTS 将文本转为语音（用于翻译模式英文输出）"""
    if not Path(EDGE_TTS_SCRIPT).exists():
        print(f"[c2e] Edge TTS script not found, skipping audio: {EDGE_TTS_SCRIPT}", file=sys.stderr)
        return None
    try:
        node_env = None
        if EDGE_TTS_MODULE_PATH:
            node_module_dir = str(Path(EDGE_TTS_MODULE_PATH).parent)
            node_env = {**os.environ, "NODE_PATH": node_module_dir}
        run_cmd(
            [NODE_BIN, EDGE_TTS_SCRIPT, text, "--voice", "en-US-AriaNeural", "--output", str(out_mp3)],
            env=node_env,
        )
        return out_mp3
    except Exception as e:
        print(f"[c2e] TTS error: {e}, skipping audio", file=sys.stderr)
        return None


def transcribe_audio(audio_path: Path) -> str:
    """使用 Whisper 将音频转录为中文文本
    - 若 WHISPER_BIN 设定了路径，调用 whisper CLI
    - 否则使用 faster-whisper（tiny + int8 CPU，已本地缓存）
    """
    if WHISPER_BIN:
        result = subprocess.run(
            [WHISPER_BIN, str(audio_path),
             "--model", "tiny", "--task", "transcribe",
             "--language", "zh", "--output_format", "txt",
             "--output_dir", str(TMP_DIR)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "whisper CLI failed")
        txt_path = TMP_DIR / f"{audio_path.stem}.txt"
        return txt_path.read_text(encoding="utf-8").strip()
    else:
        # Use faster-whisper (CTranslate2 model, ~8x faster than PyTorch)
        from faster_whisper import WhisperModel
        model = WhisperModel(FASTER_WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio_path), language="zh", beam_size=1)
        return "".join(s.text for s in segments).strip()


def translate_and_speak(text: str) -> dict:
    """
    翻译文本并生成语音
    返回: {"english": str, "audio_path": str}
    """
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    english = translate_zh_to_en(text)
    out_mp3 = TMP_DIR / f"c2e_{os.getpid()}_{len(text)}.mp3"
    audio_path = tts_edge(english, out_mp3)

    return {
        "english": english,
        "audio_path": str(audio_path) if audio_path else "",
    }


def process_voice(voice_path: str) -> dict:
    """
    处理语音消息：Whisper 转录 → 翻译 → TTS
    返回: {"chinese": str, "english": str, "audio_path": str}
    """
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = Path(voice_path)

    chinese = transcribe_audio(audio_path)
    english = translate_zh_to_en(chinese)
    out_mp3 = TMP_DIR / f"c2e_voice_{os.getpid()}_{audio_path.stem}.mp3"
    audio_path_result = tts_edge(english, out_mp3)

    return {
        "chinese": chinese,
        "english": english,
        "audio_path": str(audio_path_result) if audio_path_result else "",
    }


def handle_c2e_mode_command(text: str) -> Optional[str]:
    """
    处理 C2E 模式命令
    "翻译模式" / "c2e" → 进入翻译模式
    "解除模式" / "c2e-exit" → 退出翻译模式
    返回: 回复文本或 None（不处理）
    """
    text = text.strip()

    if text in ("翻译模式", "c2e"):
        save_c2e_mode("c2e")
        return "已进入翻译模式，请发送中文文本或语音~"

    if text in ("解除模式", "c2e-exit"):
        clear_c2e_mode()
        return "已解除翻译模式，模式已清空"

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C2E 翻译模式处理器")
    parser.add_argument("--text", help="中文文本输入（手动输入）")
    parser.add_argument("--voice", help="语音文件路径（自动转写）")
    parser.add_argument("--chinese-text", help="微信已转写的中文文本（跳过 Whisper，直接翻译）")
    parser.add_argument("--output", default="text", choices=["text", "json"], help="输出格式")
    args = parser.parse_args()

    try:
        if args.text:
            result = translate_and_speak(args.text)
            if args.output == "json":
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(result["english"])
        elif args.voice:
            result = process_voice(args.voice)
            if args.output == "json":
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(result["english"])
        elif args.chinese_text:
            english = translate_zh_to_en(args.chinese_text)
            out_mp3 = TMP_DIR / f"c2e_text_{os.getpid()}.mp3"
            audio_path_result = tts_edge(english, out_mp3)
            result = {"chinese": args.chinese_text, "english": english, "audio_path": str(audio_path_result) if audio_path_result else ""}
            if args.output == "json":
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(result["english"])
        else:
            parser.print_help()
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)