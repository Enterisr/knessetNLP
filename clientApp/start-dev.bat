@echo off
echo Starting development servers...

echo Starting FastAPI server...
set DEVELOPMENT=true
start "FastAPI Server" cmd /k "cd /d %~dp0 && python server.py"

timeout /t 3 /nobreak > nul

echo Starting React dev server...
start "React Dev Server" cmd /k "cd /d %~dp0reactApp && npm run dev"

echo Development servers started!
echo React app: http://localhost:5173
echo FastAPI server: http://localhost:3000
pause