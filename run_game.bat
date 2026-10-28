@echo off
setlocal
cd /d "%~dp0"

py -3.12 -c "import pico2d, transitions" >nul 2>&1
if errorlevel 1 (
    echo Installing game dependencies for Python 3.12...
    py -3.12 -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install game dependencies.
        pause
        exit /b 1
    )
)

py -3.12 main.py
if errorlevel 1 pause
