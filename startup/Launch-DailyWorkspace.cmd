@echo off
setlocal

set "SCRIPT_DIR=%USERPROFILE%\.agents\startup"
set "SCRIPT_PATH=%SCRIPT_DIR%\Launch-DailyWorkspace.ps1"

if not exist "%SCRIPT_PATH%" (
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%SCRIPT_PATH%"
