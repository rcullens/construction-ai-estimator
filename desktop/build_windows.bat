@echo off
echo Installing build dependencies...
pip install -r ..\requirements.txt
pip install pyinstaller flet
echo Building executable...
pyinstaller --noconfirm build_exe.spec
echo Executable: dist\ConstructionAI_Estimator.exe
pause
