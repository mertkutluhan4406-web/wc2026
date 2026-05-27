@echo off
title WC26 Compare Engine Launcher
echo =========================================
echo    WC26 COMPARE ENGINE - STARTUP SYSTEM
echo =========================================
echo.

echo [0/3] Cleaning Next.js cache (.next) to prevent hydration freeze...
if exist "frontend\.next" (
    rd /s /q "frontend\.next"
    echo Cache cleared successfully.
) else (
    echo No old cache folder found.
)
echo.

echo [1/3] Starting Python FastAPI Backend on port 8000...
start cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo [2/3] Starting Next.js Dev Server on port 3000...
start cmd /k "cd frontend && npm run dev"

echo.
echo -----------------------------------------
echo Sistem Baslatildi!
echo -^> Analiz Arayuzu: http://localhost:3000
echo -^> OBS Yayin Arayuzu: http://localhost:3000/obs
echo -^> Backend Dokumantasyonu: http://localhost:8000/docs
echo -----------------------------------------
echo Pencereleri kapatarak sunuculari durdurabilirsiniz.
pause
