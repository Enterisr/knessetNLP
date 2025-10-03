# PowerShell script to start both development servers
Write-Host "Starting development servers..." -ForegroundColor Green

# Start FastAPI server in development mode
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
$env:DEVELOPMENT = "true"
Start-Process powershell -ArgumentList "-Command", "cd '$PSScriptRoot'; python server.py" -WindowStyle Normal

# Wait a moment for the API server to start
Start-Sleep -Seconds 3

# Start React dev server
Write-Host "Starting React dev server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd '$PSScriptRoot\reactApp'; npm run dev" -WindowStyle Normal

Write-Host "Development servers started!" -ForegroundColor Green
Write-Host "React app: http://localhost:5173" -ForegroundColor Cyan
Write-Host "FastAPI server: http://localhost:3000" -ForegroundColor Cyan


Write-Host "Press any key to exit..." -ForegroundColor Gray
Read-Host