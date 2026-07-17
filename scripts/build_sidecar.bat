@echo off
setlocal
echo ==> Installing dependencies...
pip install -r ..\requirements.txt
pip install pyinstaller fastapi uvicorn python-multipart
echo ==> Building Python sidecar...
pyinstaller --noconfirm --onefile --name python-sidecar --paths .. ^
  --add-data "..\prompts;prompts" --add-data "..\config;config" --add-data "..\models;models" ^
  --add-data "..\agents;agents" --add-data "..\ingestion;ingestion" --add-data "..\visualization;visualization" ^
  --add-data "..\utils;utils" --hidden-import uvicorn --hidden-import fastapi --collect-all uvicorn --collect-all fastapi ^
  ..\python-sidecar\main.py
if not exist "src-tauri\binaries" mkdir src-tauri\binaries
copy /Y dist\python-sidecar.exe src-tauri\binaries\python-sidecar-x86_64-pc-windows-msvc.exe
echo Sidecar built: src-tauri\binaries\python-sidecar-x86_64-pc-windows-msvc.exe
echo Next: cd src-tauri && cargo tauri build
pause
