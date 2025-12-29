@echo off
set CONDA_PATH=E:\apps\miniconda3
call %CONDA_PATH%\Scripts\activate.bat pytorch_python11

REM Initialize MSVC Compiler (Required for JIT)
set VCVARS="C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if exist %VCVARS% (
    call %VCVARS% >nul 2>&1
) else (
    echo Warning: vcvars64.bat not found. JIT compilation might fail if not already cached.
)

echo Starting Global Copilot (RTX 5070 Ti Edition)...
echo Speed Target: >80 t/s (ExLlamaV2)
echo Status: Waiting for input in any app...
python main_client.py
pause
