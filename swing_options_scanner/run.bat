@echo off
REM ─────────────────────────────────────────────────────────
REM  Swing Options Scanner — Windows launcher
REM ─────────────────────────────────────────────────────────
setlocal
cd /d "%~dp0"

echo.
echo === Swing Options Scanner ===
echo.

REM Optional: install/refresh dependencies quietly
python -m pip install -q -r requirements.txt

REM Run the scanner (defaults: BOTH directions, $110 USD budget, opens browser)
python scanner.py %*

endlocal
pause