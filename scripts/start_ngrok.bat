@echo off
call "%~dp0netrava.bat" start ngrok
exit /b %errorlevel%
