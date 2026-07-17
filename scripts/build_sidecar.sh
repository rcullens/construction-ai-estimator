#!/usr/bin/env bash
# Build the Python sidecar as a standalone binary for Tauri
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller fastapi uvicorn python-multipart
echo "==> Detecting platform..."
OS="$(uname -s)"; ARCH="$(uname -m)"
case "$OS" in
  Linux*) TRIPLE="x86_64-unknown-linux-gnu"; [[ "$ARCH" == "aarch64" ]] && TRIPLE="aarch64-unknown-linux-gnu" ;;
  Darwin*) if [[ "$ARCH" == "arm64" ]]; then TRIPLE="aarch64-apple-darwin"; else TRIPLE="x86_64-apple-darwin"; fi ;;
  *) echo "Unsupported OS: $OS"; exit 1 ;;
esac
echo "    Target triple: $TRIPLE"
OUT_DIR="src-tauri/binaries"; mkdir -p "$OUT_DIR"
echo "==> Running PyInstaller..."
pyinstaller --noconfirm --onefile --name "python-sidecar" --paths . \
  --add-data "prompts:prompts" --add-data "config:config" --add-data "models:models" \
  --add-data "agents:agents" --add-data "ingestion:ingestion" --add-data "visualization:visualization" \
  --add-data "utils:utils" --hidden-import uvicorn --hidden-import fastapi --collect-all uvicorn --collect-all fastapi \
  python-sidecar/main.py
cp dist/python-sidecar "$OUT_DIR/python-sidecar-$TRIPLE"
chmod +x "$OUT_DIR/python-sidecar-$TRIPLE"
echo "Sidecar built: $OUT_DIR/python-sidecar-$TRIPLE"
echo "Next: cd src-tauri && cargo tauri build"
