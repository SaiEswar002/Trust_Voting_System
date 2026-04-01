@echo off
cd /d "%~dp0"
echo Initializing network...

REM Terminate existing python app.py instances
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Clean shared keys
if exist backend\shared_keys.json del backend\shared_keys.json

echo Booting 6-Node Voting Network!

start "Node1" cmd /k "..\..\.venv\Scripts\activate.bat && python app.py 5001 1"
timeout /t 3 /nobreak >nul

start "Node2" cmd /k "..\..\.venv\Scripts\activate.bat && python app.py 5002 2"

start "Node3" cmd /k "..\..\.venv\Scripts\activate.bat && python app.py 5003 3"

start "Node4" cmd /k "..\..\.venv\Scripts\activate.bat && python app.py 5004 4"

start "Node5" cmd /k "..\..\.venv\Scripts\activate.bat && python app.py 5005 5"

start "Node6" cmd /k "..\..\.venv\Scripts\activate.bat && python app.py 5006 6"

echo All nodes started! Access booths at http://127.0.0.1:5001 etc.
echo Use taskkill /f /im python.exe to stop.
pause
