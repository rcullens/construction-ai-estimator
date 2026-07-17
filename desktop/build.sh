#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "Installing build dependencies..."
pip install -r ../requirements.txt
pip install pyinstaller flet
echo "Building executable..."
pyinstaller --noconfirm build_exe.spec
echo "Executable is in: dist/ConstructionAI_Estimator"
