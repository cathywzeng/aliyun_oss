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
MISSING_PYTHON=""
python3 -c "import openai" 2>/dev/null || MISSING_PYTHON="$MISSING_PYTHON openai"
python3 -c "import requests" 2>/dev/null || MISSING_PYTHON="$MISSING_PYTHON requests"
if [ -n "$MISSING_PYTHON" ]; then
    echo "⚠️  Missing: $MISSING_PYTHON"
    echo "   Install: pip install$MISSING_PYTHON"
else
    echo "✅ Python dependencies OK"
fi

# 4. Check Node.js and edge-tts
echo "=== Checking Node.js ==="

# Try standard PATH first, then common non-standard locations
NODE_BIN=""
for p in node "/opt/homebrew/bin/node" "$HOME/.nvm/versions/node/*/bin/node"; do
    if [ -x "$p" ] 2>/dev/null || command -v "$p" &>/dev/null; then
        NODE_BIN="$p"
        break
    fi
done

NPM_BIN=""
for p in npm "/opt/homebrew/bin/npm" "$HOME/.nvm/versions/node/*/bin/npm"; do
    if [ -x "$p" ] 2>/dev/null || command -v "$p" &>/dev/null; then
        NPM_BIN="$p"
        break
    fi
done

if [ -n "$NODE_BIN" ]; then
    echo "✅ Node.js found: $("$NODE_BIN" --version)"
    if [ -n "$NPM_BIN" ]; then
        if "$NPM_BIN" list -g node-edge-tts &>/dev/null; then
            echo "✅ node-edge-tts installed"
        else
            echo "⚠️  node-edge-tts not installed (run: $NPM_BIN install -g node-edge-tts)"
        fi
    else
        echo "⚠️  npm not found (Node.js at $NODE_BIN)"
    fi
else
    echo "⚠️  Node.js not found"
    echo "   Install from: https://nodejs.org/"
    echo "   Or on macOS: brew install node"
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
