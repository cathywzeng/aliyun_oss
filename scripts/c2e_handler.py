#!/usr/bin/env python3
"""
C2E (Chinese→English) 翻译模式处理器
整合 Ollama 翻译 + Edge TTS 语音合成 + Whisper 语音识别
用于微信渠道的实时翻译模式
"""

import json
import os
import sys
import argparse
import re
import subprocess
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Mode file path (shared with aliyun-oss)
MODE_PATH = os.environ.get("MODE_PATH", "~/.openclaw/memory/weixin_mode.json")

# MiniMax Anthropic-compatible API (for translation)
MINIMAX_API_KEY = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
MINIMAX_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_BIN = os.environ.get("OLLAMA_BIN", "ollama")
WHISPER_BIN = os.environ.get("WHISPER_BIN", "whisper")
NODE_BIN = os.environ.get("NODE_BIN", "node")
EDGE_TTS_SCRIPT = os.environ.get(
    "EDGE_TTS_SCRIPT",
    str(Path(__file__).parent.parent / "c2e" / "tts-converter.js")
)
TMP_DIR = Path(os.environ.get("TMP_DIR", "/tmp/c2e-wechat"))


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


def run_cmd(cmd: list[str], timeout: int = 120) -> str:
    """执行命令并返回 stdout"""
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"command failed: {' '.join(cmd)}")
    return p.stdout.strip()


def clean_ollama(text: str) -> str:
    """清理 ANSI 控制字符"""
    text = re.sub(r"\x1B\[[0-9;?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    return text.strip()


def translate_zh_to_en(chinese: str) -> str:
    """使用 MiniMax Anthropic-compatible API 将中文翻译为英文"""
    if MINIMAX_API_KEY and MINIMAX_BASE_URL:
        try:
            import requests
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
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            # Anthropic messages API returns content as a list
            content = data.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if block.get("type") == "text":
                        return block["text"].strip()
            return str(content)
        except Exception as e:
            print(f"[c2e] MiniMax API error: {e}, falling back to Ollama", file=sys.stderr)

    # Fallback to Ollama
    prompt = (
        "Translate the following Chinese to English. "
        "Keep names, numbers, dates, and IDs exact. "
        "Do not add facts. Output only English text in natural style.\n\n"
        f"Chinese:\n{chinese}"
    )
    out = run_cmd([OLLAMA_BIN, "run", OLLAMA_MODEL, prompt])
    return clean_ollama(out) or "(translation failed)"


def tts_edge(text: str, out_mp3: Path) -> Path | None:
    """使用 Edge TTS 将英文文本转为语音"""
    if not Path(EDGE_TTS_SCRIPT).exists():
        print(f"[c2e] Edge TTS script not found, skipping audio: {EDGE_TTS_SCRIPT}", file=sys.stderr)
        return None
    try:
        run_cmd([
            NODE_BIN,
            EDGE_TTS_SCRIPT,
            text,
            "--voice", "en-US-AriaNeural",
            "--output", str(out_mp3),
        ])
        return out_mp3
    except Exception as e:
        print(f"[c2e] TTS error: {e}, skipping audio", file=sys.stderr)
        return None


def transcribe_audio(audio_path: Path) -> str:
    """使用 Whisper 将音频转录为中文文本"""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        WHISPER_BIN, str(audio_path),
        "--model", "turbo",
        "--task", "transcribe",
        "--output_format", "txt",
        "--output_dir", str(TMP_DIR),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "whisper failed")
    txt_path = TMP_DIR / f"{audio_path.stem}.txt"
    if not txt_path.exists():
        raise RuntimeError(f"transcript file not found")
    return txt_path.read_text(encoding="utf-8").strip()


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


def handle_c2e_mode_command(text: str) -> str | None:
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
    parser.add_argument("--text", help="中文文本输入")
    parser.add_argument("--voice", help="语音文件路径")
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
        else:
            parser.print_help()
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)