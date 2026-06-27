@echo off
cd /d "%~dp0"
start "" /min py app.py
timeout /t 2 /nobreak >nul
start chrome "http://localhost:5000"
