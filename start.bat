@echo off
echo Starting EcoVision AI+ Backend...
cd /d "c:\Users\smart\Desktop\python project\eco_build_ai\backend"
start cmd /k "python -m pip install -r requirements.txt && python -m uvicorn app.main:app --reload"

echo Starting EcoVision AI+ Frontend...
cd /d "c:\Users\smart\Desktop\python project\eco_build_ai\frontend"
start cmd /k "npm install && npm run dev"

echo.
echo Both servers are starting up in separate windows!
echo - The Backend will be available at http://localhost:8000
echo - The Frontend Dashboard will be available at http://localhost:5173
pause
