
# run_webview.ps1
$ErrorActionPreference = "Stop"

Write-Host "Starting A8 Whisper (Pywebview Unified)..." -ForegroundColor Cyan

# Cleanup existing processes to prevent port conflicts
Write-Host "🧹 Cleaning up zombie processes..." -ForegroundColor Gray
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process msedge -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -match "A8轻语"} | Stop-Process -Force

$env:A8_DEV_MODE = "1" # Enable Hot Reload (Dev Server)

# Check if frontend needs rebuild
$distPath = "gui_web\dist\index.html"
$srcPath = "gui_web\src"


if (-not (Test-Path $distPath)) {
    Write-Host "⚠️  Frontend not built. Building now..." -ForegroundColor Yellow
    Push-Location gui_web
    npm run build
    Pop-Location    
} else {
    # Check if src is newer than dist
    $distTime = (Get-Item $distPath).LastWriteTime
    $srcFiles = Get-ChildItem -Path $srcPath -Recurse -File
    $newestSrc = ($srcFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    
    if ($newestSrc -gt $distTime) {
        Write-Host "⚠️  Source files changed. Rebuilding frontend..." -ForegroundColor Yellow
        Push-Location gui_web
        npm run build
        Pop-Location
    } else {
        Write-Host "✅ Frontend is up-to-date" -ForegroundColor Green
    }
}

# Set environment
$env:PYTHONPATH = "$PWD"

# Run Python (which now manages Vite automatically)
.venv\Scripts\python src/main_webview.py
