@echo off
cd /d "%~dp0"
echo [1/3] Installing / checking Playwright...
py -3 -m pip install playwright --quiet
py -3 -m playwright install chromium
echo [2/3] Running screenshot capture script...
py -3 scripts\capture_screenshots.py
echo.
echo [3/3] Listing captured proofs:
dir /b Exploitation\Proofs\*.png 2>nul || echo No PNGs found yet.
pause
