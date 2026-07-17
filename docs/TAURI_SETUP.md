# Tauri 2 Setup & Build Guide

This project uses **Tauri 2** with a **Python sidecar**.

Architecture:
- Frontend: Vite + plain HTML/JS (in `/ui`)
- Desktop shell: Tauri 2 (Rust) in `/src-tauri`
- Backend logic: existing Python code exposed via FastAPI sidecar (`/python-sidecar`)

## Prerequisites

- Node.js 20+
- Rust (https://rustup.rs)
- Python 3.11 or 3.12
- Platform build tools (C++ Build Tools on Windows, Xcode CLT on macOS, webkit deps on Linux)

## Development

```bash
# Python sidecar
pip install -r requirements.txt fastapi uvicorn python-multipart
cd python-sidecar && python main.py

# Frontend + Tauri (separate terminal)
cd ui && npm install
cd ../src-tauri && cargo tauri dev
```

## Production Build

1. Build the Python sidecar:
   - Linux/macOS: `./scripts/build_sidecar.sh`
   - Windows: `scripts\build_sidecar.bat`

2. Build Tauri app:
   ```bash
   cd src-tauri
   cargo tauri build
   ```

Output appears in `src-tauri/target/release/bundle/`.

See also `scripts/` for the improved packaging helpers and `src-tauri/icons/README.md` for icon generation.
