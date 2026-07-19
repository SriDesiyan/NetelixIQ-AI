

# NetElixIQ AI Startup Script (PowerShell)
# Run from the project root directory

Write-Host "NetElixIQ AI - Starting up..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Start Backend
Write-Host "`n[1/2] Starting FastAPI Backend (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "[2/2] Starting Vite Frontend (port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "`n======================================" -ForegroundColor Green
Write-Host "NetElixIQ AI is starting!" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "======================================" -ForegroundColor Green
