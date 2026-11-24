@echo off
REM ============================================================
REM  Options Day Trader launcher (9:30 AM - 12:00 PM ET session)
REM ============================================================
cd /d "%~dp0"

REM pip install -r requirements.txt

python daytrader.py %*

pause