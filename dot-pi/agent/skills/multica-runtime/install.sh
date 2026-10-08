#!/bin/bash
# install.sh — Installs multica-llm-runtime as system command
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="/usr/local/bin/multica-llm-runtime"

# Copy from src/
echo "Installing multica-llm-runtime to $TARGET..."
sudo cp "$SCRIPT_DIR/src/multica-llm-runtime.py" "$TARGET"
sudo chmod +x "$TARGET"

echo "✅ Installed. Test with:"
echo "   multica-llm-runtime info"
echo "   multica-llm-runtime health-check"
echo "   multica-llm-runtime execute MUL-123 --llm text:\"You code.\" --dry-run"
