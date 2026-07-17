# Construction AI Estimator

AI-powered desktop application that parses construction blueprints, specifications, project manuals and addenda, then breaks every job responsibility down by trade with full auditability and interactive chat.

## Architecture (Primary Path)

**Tauri 2 + Python Sidecar**

- **Frontend**: Modern lightweight web UI (Vite)
- **Desktop shell**: Tauri 2 (Rust) – small, secure, native
- **Backend**: All existing Python intelligence (agents, Digital Twins, LLM, visualization) exposed as a local FastAPI sidecar

See full setup & build instructions: **[docs/TAURI_SETUP.md](docs/TAURI_SETUP.md)**

## Quick Development Start (Tauri)

```bash
# Terminal 1 – Python sidecar
pip install -r requirements.txt fastapi uvicorn python-multipart
cd python-sidecar
python main.py

# Terminal 2 – Frontend + Tauri
cd ui && npm install && cd ..
cd src-tauri
cargo tauri dev
```

## Alternative Launchers

```bash
# Flet desktop (pure Python)
python desktop/main.py

# Streamlit web
streamlit run app/streamlit_app.py

# CLI batch
python run_analysis.py --project-name "My Job" ./plans/*.pdf
```

## Features

- Multi-agent analysis with Completeness Auditor
- Grounded extraction (every item has source text)
- Editable trade names + fully custom trades
- Explicit cross-trade assignment support with `override_reason`
- Interactive chat with full project context
- 2D plan viewer + upgraded multi-level 3D massing
- Export to JSON + Excel
- Packages as a single native desktop app via Tauri 2

## Project Layout

```
construction-ai-estimator/
├── src-tauri/              # Tauri 2 (Rust shell)
├── ui/                     # Frontend (Vite)
├── python-sidecar/         # FastAPI wrapper around the Python core
├── desktop/                # Flet version
├── app/                    # Streamlit version
├── models/ agents/ ingestion/ visualization/ prompts/
├── scripts/                # Sidecar build scripts
└── docs/TAURI_SETUP.md     # Full Tauri build guide
```
