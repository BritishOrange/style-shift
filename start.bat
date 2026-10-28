@echo off
chcp 65001 >nul
setlocal

where poetry >nul 2>&1
if errorlevel 1 (
  echo Poetry not found. Install it first:
  echo   py -3 -m pip install poetry
  pause
  exit /b 1
)

echo Ensuring in-project virtualenv...
poetry config virtualenvs.in-project true --local
poetry install
if errorlevel 1 (
  echo Failed to install dependencies via Poetry.
  pause
  exit /b 1
)

echo.
echo Starting StyleShift...
poetry run styleshift
pause
