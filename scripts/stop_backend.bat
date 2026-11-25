@echo off
call "%~dp0netrava.bat" stop backend
exit /b %errorlevel%
