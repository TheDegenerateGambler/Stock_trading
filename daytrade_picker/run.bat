# @echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  DAYTRADE PICKER
echo ============================================================
echo.

echo [1/2] Installing dependencies...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)
echo     OK
echo.

echo [2/2] Starting DayTrade Picker...
echo       Report will open at http://127.0.0.1:8766/report.html
echo       Press Ctrl+C to stop.
echo.
python pick.py

pause