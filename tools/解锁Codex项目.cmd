@echo off
chcp 65001 >nul
set PY=C:\Users\zbh\AppData\Local\Programs\Python\Python312\python.exe
echo === 解锁 Codex 的 ChatGPT 项目镜像目录 ===
if "%~1"=="" (
  for /d %%d in ("%USERPROFILE%\.codex\.chatgpt-projects\g-p-*") do (
    "%PY%" "%~dp0unlock_codex_project.py" --kill "%%~fd"
  )
) else (
  "%PY%" "%~dp0unlock_codex_project.py" --kill "%USERPROFILE%\.codex\.chatgpt-projects\%~1"
)
echo.
echo === 完成。回到 Codex，不重启，直接点项目新建本地聊天 ===
pause
