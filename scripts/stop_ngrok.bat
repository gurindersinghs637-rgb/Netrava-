@echo off
call "%~dp0netrava.bat" stop ngrok
exit /b %errorlevel%
