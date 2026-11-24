@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Is Python installed and on PATH?
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

if "%~1"=="" (
    echo.
    echo Usage examples:
    echo   run_cc.bat --buy-write
    echo   run_cc.bat --positions BTO.TO:5.20:100 BB.TO:4.80:100
    echo   run_cc.bat --buy-write --run-puts
    echo.
    ".venv\Scripts\python.exe" scan_cc.py --help
    exit /b 0
)

".venv\Scripts\python.exe" scan_cc.py %*
endlocal