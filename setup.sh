#!/bin/bash
# curiousbuddy setup script for fresh install
set -e

echo "=== curiousbuddy Setup ==="

# 0. Check if already installed
if [ -d ~/.openclaw/skills/curiousbuddy ]; then
    echo "⚠️  curiousbuddy already exists at ~/.openclaw/skills/curiousbuddy"
    echo "   Pull latest: cd ~/.openclaw/skills/curiousbuddy && git pull"
    echo "   Or remove it first to re-install"
    exit 0
fi

# 1. Clone latest curiousbuddy from GitHub
echo "=== Cloning curiousbuddy ==="
SKILL_DIR="$(mktemp -d)"
git clone https://github.com/cathywzeng/curiousbuddy.git "$SKILL_DIR"
cd "$SKILL_DIR"
git checkout master
echo "✅ Cloned to $SKILL_DIR"

# 2. Deploy to ~/.openclaw/skills/curiousbuddy
echo "=== Deploying to ~/.openclaw/skills/curiousbuddy ==="
mkdir -p ~/.openclaw/skills
mv "$SKILL_DIR" ~/.openclaw/skills/curiousbuddy
echo "✅ Deployed"

# 3. Create memory directory
mkdir -p ~/.openclaw/memory

# 4. Install Node.js dependencies for trsl
echo "=== Installing trsl Node.js dependencies ==="
if [ -d ~/.openclaw/skills/curiousbuddy/trsl ]; then
    (cd ~/.openclaw/skills/curiousbuddy/trsl && npm install)
    echo "✅ trsl npm dependencies installed"
else
    echo "⚠️  trsl directory not found, skipping npm install"
fi

# 2. Check env_config.json
if [ ! -f ~/.openclaw/memory/env_config.json ]; then
    echo "⚠️  env_config.json not found, copying template..."
    cp ~/.openclaw/skills/curiousbuddy/env_config.json ~/.openclaw/memory/env_config.json 2>/dev/null || true
    echo "⚠️  Please edit ~/.openclaw/memory/env_config.json with your real credentials"
    echo "   - Set NODE_BIN to your node path if not in PATH"
    echo "   - Set EDGE_TTS_MODULE_PATH to your npm global modules path"
else
    echo "✅ env_config.json exists"
fi

# 3. Install Python dependencies
echo "=== Installing Python dependencies ==="
if [ -f ~/.openclaw/skills/curiousbuddy/requirements.txt ]; then
    python3 -m pip install --quiet -r ~/.openclaw/skills/curiousbuddy/requirements.txt 2>/dev/null && echo "✅ Python dependencies installed" || echo "⚠️  pip install failed"
else
    echo "⚠️  requirements.txt not found"
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
if python3 ~/.openclaw/skills/curiousbuddy/scripts/check_and_patch.py; then
    echo "✅ Patch applied"
else
    echo "⚠️  Patch failed"
fi

echo "=== Setup complete ==="
echo "Restart OpenClaw gateway to apply changes."
