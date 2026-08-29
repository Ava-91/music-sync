@echo off
setlocal
cd /d "%~dp0"
python app.py
if errorlevel 1 (
    echo.
    echo music-sync could not start. Make sure Python 3.11+ is installed
    echo and run install.bat first.
    pause
)
endlocal
