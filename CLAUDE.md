# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`curiousbuddy` is an OpenClaw skill for WeChat integration providing AI-powered problem-solving/correction and Chinese-to-English translation. It integrates with Aliyun OSS, DashScope API (通义千问), Edge TTS, and Whisper.

## Key Commands

### Run Tests
```bash
# Run all trsl_handler tests
python3 scripts/test_trsl_handler.py

# Run a specific test class
python3 -m pytest scripts/test_trsl_handler.py::TestTRSLModeManagement -v
```

### Patch Management
```bash
python3 ~/.openclaw/skills/curiousbuddy/scripts/check_and_patch.py
```

## Architecture

The skill has two independent modes stored in `~/.openclaw/memory/weixin_mode.json`:

**Aliyun Mode** (`aliyun_handler.py`) — Photo upload → OSS upload → DashScope API → LaTeX answer
**TRSL Mode** (`trsl_handler.py`) — Chinese text/voice → MiniMax/Ollama translate → Edge TTS speak

Both modes can be active simultaneously (stored as separate keys in the mode JSON).

### Core Scripts

| File | Role |
|------|------|
| `scripts/aliyun_handler.py` | Problem-solving/correction orchestration |
| `scripts/trsl_handler.py` | TRSL translation mode (translate + TTS + Whisper) |
| `scripts/oss_uploader.py` | Aliyun OSS upload utility |
| `scripts/call_api.py` | DashScope API caller |
| `scripts/latex_to_unicode.py` | LaTeX → Unicode conversion |
| `scripts/check_and_patch.py` | Detects version mismatches and applies patches |
| `trsl/tts-converter.js` | Node.js Edge TTS wrapper |

### Mode State

Mode state lives at `~/.openclaw/memory/weixin_mode.json`:
```json
{"aliyun": "解题模式", "trsl": "trsl"}
```

`trsl_handler.py` exposes `load_trsl_mode()`, `save_trsl_mode()`, `clear_trsl_mode()` for mode state management. TRSL mode takes priority when exiting (clears only trsl key, preserves aliyun).

### Translation Pipeline (TRSL)

1. Text → MiniMax `/v1/messages` API (with `MINIMAX_API_KEY`)
2. Fallback → Ollama local model (if MiniMax key empty)
3. English text → Edge TTS via `trsl/tts-converter.js` (Node.js, requires `node-edge-tts`)
4. Voice input → Whisper CLI transcription before translation

### Dependencies

- Python: `openai` (for MiniMax), `requests`
- Node.js: `node-edge-tts`, `commander` (in `trsl/`)
- System: `whisper` CLI (for voice transcription)

### Configuration (not committed)

Written to `~/.openclaw/memory/env_config.json`:
- `oss_bucket`, `oss_region`, `oss_access_key`, `oss_secret`
- `dashscope_api_key`, `dashscope_app_id`
- `MINIMAX_API_KEY` (env var for trsl_handler)

## Patch System

Patches in `patches/` target specific `openclaw-weixin` versions. `check_and_patch.py` compares plugin version, applies missing patches, and logs to `~/.openclaw/skills/curiousbuddy/patch_history.json`.
