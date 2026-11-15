@echo off
rem Starts the Jarvis server (minimized) and opens it as its own app window in Edge.
cd /d "%~dp0"
start "Jarvis Server" /min python jarvis_server.py --no-browser
timeout /t 3 /nobreak >nul
start "" msedge --app=http://localhost:8000
