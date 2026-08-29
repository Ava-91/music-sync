@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Dependency installation failed.
    pause
    exit /b 1
)
echo.
echo Dependencies installed successfully. You can now run run.bat.
pause
endlocal
