@echo off
REM ==========================================================================
REM  wheel.bat — one-click wheel dashboard
REM
REM  Runs every scanner (monthly + weekly, puts + calls, TSX + US),
REM  builds ONE HTML page with a top-10 leaderboard + all sections,
REM  and opens it in your default browser.
REM
REM  Just double-click me. No flags, no config.
REM ==========================================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment ^(one-time setup, may take a minute^)...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment.
        echo Is Python installed and on your PATH?
        echo Download it from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo Installing dependencies...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo.
echo ================================================================
echo   Running the WHEEL — all sections
echo   This can take 3–6 minutes depending on Yahoo Finance speed.
echo ================================================================
echo.

".venv\Scripts\python.exe" run_all.py
set RC=%ERRORLEVEL%

if not exist "output\wheel_dashboard.html" (
    echo.
    echo ERROR: Dashboard was not generated. See errors above.
    pause
    exit /b 1
)

echo.
echo Opening dashboard in your default browser...
start "" "output\wheel_dashboard.html"

echo.
echo Done. Report saved at: %CD%\output\wheel_dashboard.html
echo.
endlocal
exit /b %RC%