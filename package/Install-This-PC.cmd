@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-This-PC.ps1"
echo.
echo Review the result above. Then open Codex and use /hooks to trust the three project-memory hooks.
pause
