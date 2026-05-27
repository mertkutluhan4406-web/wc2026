# WC26 Compare Engine - Full Stack Startup Script (PowerShell)
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   WC26 COMPARE ENGINE - STARTUP SYSTEM  " -ForegroundColor Gold
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start FastAPI Backend in a new window
Write-Host "[1/2] Starting Python FastAPI Backend on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"

# 2. Start Next.js Frontend in a new window
Write-Host "[2/2] Starting Next.js Dev Server on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "-----------------------------------------" -ForegroundColor Slate
Write-Host "Sistem Başlatıldı!" -ForegroundColor Green
Write-Host "-> Analiz Arayüzü: http://localhost:3000" -ForegroundColor Cyan
Write-Host "-> OBS Yayın Arayüzü: http://localhost:3000/obs" -ForegroundColor Cyan
Write-Host "-> Backend Dokümantasyonu: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "-----------------------------------------" -ForegroundColor Slate
Write-Host "Pencereleri kapatarak sunucuları durdurabilirsiniz." -ForegroundColor Slate
