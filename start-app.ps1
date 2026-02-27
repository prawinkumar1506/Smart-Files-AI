# Smart Files AI Startup Script
Write-Host "[*] Starting Smart Files AI..." -ForegroundColor Cyan

# Kill any existing processes on required ports
Write-Host "[*] Cleaning up ports..." -ForegroundColor Yellow
node kill-ports.js

Start-Sleep -Seconds 1

# Start Backend in new terminal
Write-Host "[*] Starting Backend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python -m uvicorn main:app --reload --port 8000"

# Build Next.js once if not already built (much faster on subsequent runs)
if (!(Test-Path "out")) {
    Write-Host "[*] Building Next.js frontend (first run only)..." -ForegroundColor Yellow
    pnpm build
}

# Start simple HTTP server for built Next.js
Write-Host "[*] Starting Frontend Server on port 3001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; node serve-frontend.js"

# Wait for servers to start
Write-Host "[*] Waiting for servers to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Start Tauri Desktop App
Write-Host "[*] Launching Desktop Application..." -ForegroundColor Magenta
pnpm tauri dev

Write-Host "[OK] Application started successfully!" -ForegroundColor Green
