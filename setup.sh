#!/bin/bash
# curiousbuddy setup script for fresh install
set -e

echo "=== curiousbuddy Setup ==="

# 1. Create memory directory
mkdir -p ~/.openclaw/memory

# 2. Check env_config.json
if [ ! -f ~/.openclaw/memory/env_config.json ]; then
    echo "⚠️  env_config.json not found, copying from skill..."
    cp "$(dirname "$0")/env_config.json" ~/.openclaw/memory/env_config.json 2>/dev/null || true
    echo "⚠️  Please edit ~/.openclaw/memory/env_config.json with your real credentials"
else
    echo "✅ env_config.json exists"
fi

# 3. Check Python dependencies
echo "=== Checking Python dependencies ==="
python3 -c "import openai" 2>/dev/null || echo "⚠️  openai not installed (pip install openai)"
python3 -c "import requests" 2>/dev/null || echo "⚠️  requests not installed (pip install requests)"

# 4. Check Node.js and edge-tts
echo "=== Checking Node.js ==="
if command -v node &>/dev/null; then
    echo "✅ Node.js found: $(node --version)"
    if command -v npm &>/dev/null; then
        if npm list -g node-edge-tts &>/dev/null; then
            echo "✅ node-edge-tts installed"
        else
            echo "⚠️  node-edge-tts not installed (npm install -g node-edge-tts)"
        fi
    else
        echo "⚠️  npm not found"
    fi
else
    echo "⚠️  Node.js not found"
fi

# 5. Check Whisper (optional)
echo "=== Checking Whisper ==="
if command -v whisper &>/dev/null; then
    echo "✅ Whisper found"
else
    echo "⚠️  Whisper not found (optional, for voice transcription)"
fi

# 6. Apply patch to openclaw-weixin
echo "=== Applying patch ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if python3 "$SCRIPT_DIR/scripts/check_and_patch.py"; then
    echo "✅ Patch applied"
else
    echo "⚠️  Patch failed"
fi

echo "=== Setup complete ==="
echo "Restart OpenClaw gateway to apply changes."
