@echo off
set CONDA_PATH=E:\apps\miniconda3
call %CONDA_PATH%\Scripts\activate.bat pytorch_python11

echo Starting Caret Diagnostic Tool...
echo Please switch focus to VS Code, Notepad, etc.
python test_caret.py
pause
