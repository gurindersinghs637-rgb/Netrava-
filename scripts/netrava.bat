@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0netrava.ps1" %*
exit /b %errorlevel%
