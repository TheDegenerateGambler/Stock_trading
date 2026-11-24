@echo off
REM ============================================================
REM  Premarket Scanner launcher
REM ============================================================
cd /d "%~dp0"

REM Optional: install deps on first run (uncomment if desired)
REM pip install -r requirements.txt

python scanner.py %*

pause