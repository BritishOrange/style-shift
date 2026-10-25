@echo off
chcp 65001 >nul
setlocal

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set PYTHON=py -3
) else (
  set PYTHON=python
)

echo Installing dependencies...
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install dependencies. Make sure Python 3.10+ is installed.
  pause
  exit /b 1
)

echo.
echo Starting server...
%PYTHON% app.py
pause
