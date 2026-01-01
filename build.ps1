# A8轻语 Build Script for Windows
# Run this in PowerShell to build the EXE

param(
    [switch]$SkipFrontend,  # Skip frontend build if unchanged
    [switch]$Clean          # Force clean build (no cache)
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  A8轻语 Build Script (Optimized)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Step 1: Build Frontend (skip if -SkipFrontend)
if (-not $SkipFrontend) {
    Write-Host "`n[1/5] Building Frontend..." -ForegroundColor Yellow
    Push-Location gui_web
    
    # Auto-detect package manager
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        Write-Host "Using pnpm..." -ForegroundColor Gray
        cmd /c "pnpm install --prefer-offline && pnpm build"
    } elseif (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "Using npm..." -ForegroundColor Gray
        cmd /c "npm install && npm run build"
    } else {
        Write-Host "ERROR: No package manager found (npm or pnpm required)!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend build failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location

    if (-not (Test-Path "gui_web/dist/index.html")) {
        Write-Host "ERROR: Frontend build failed (dist not found)!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Frontend build complete." -ForegroundColor Green
}
else {
    Write-Host "`n[1/5] Skipping Frontend build (-SkipFrontend)" -ForegroundColor Gray
}

# Step 1.5: Clean previous build (only if -Clean)
if ($Clean) {
    Write-Host "`n[1.5/5] Cleaning previous build..." -ForegroundColor Yellow
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue }
}
else {
    Write-Host "`n[1.5/5] Using cached build artifacts (use -Clean to force rebuild)" -ForegroundColor Gray
}

# Step 2: Create ICO file from SVG (skip if exists)
Write-Host "`n[2/5] Checking icon.ico..." -ForegroundColor Yellow
if (-not (Test-Path "src/assets/icon.ico")) {
    if (Test-Path "src/assets/icon.svg") {
        cmd /c "uv run python -c ""from PIL import Image; import cairosvg; cairosvg.svg2png(url='src/assets/icon.svg', write_to='src/assets/icon_temp.png', output_width=256, output_height=256); Image.open('src/assets/icon_temp.png').save('src/assets/icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]); import os; os.remove('src/assets/icon_temp.png'); print('icon.ico generated')"""
        if ($LASTEXITCODE -ne 0) {
            Write-Host "WARNING: Failed to generate icon.ico. Trying fallback..." -ForegroundColor Yellow
            cmd /c "uv run python -c ""from PIL import Image; img = Image.new('RGB', (256, 256), (99, 102, 241)); img.save('src/assets/icon.ico', format='ICO'); print('Fallback icon.ico created')"""
        }
    }
    else {
        Write-Host "WARNING: icon.svg not found. Using fallback icon." -ForegroundColor Yellow
        cmd /c "uv run python -c ""from PIL import Image; img = Image.new('RGB', (256, 256), (99, 102, 241)); img.save('src/assets/icon.ico', format='ICO'); print('Fallback icon.ico created')"""
    }
}
else {
    Write-Host "icon.ico already exists, skipping." -ForegroundColor Gray
}

# Step 3: Install PyInstaller if needed
Write-Host "`n[3/5] Checking PyInstaller..." -ForegroundColor Yellow
try {
    cmd /c "uv run python -c ""import PyInstaller"""
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller check failed" }
}
catch {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    cmd /c "uv pip install pyinstaller"
}
Write-Host "PyInstaller ready." -ForegroundColor Green

# Step 4: Run PyInstaller with cache
Write-Host "`n[4/5] Building EXE with PyInstaller..." -ForegroundColor Yellow
$startTime = Get-Date

# Set UTF-8 encoding for build process
$env:PYTHONIOENCODING = "utf-8"

# Use --noconfirm to skip prompts, cache is in build/ folder by default
$pyiArgs = "a8qingyu.spec --noconfirm"
if ($Clean) {
    $pyiArgs += " --clean"
}

cmd /c "uv run pyinstaller $pyiArgs"

$elapsed = (Get-Date) - $startTime
Write-Host "PyInstaller completed in $($elapsed.TotalSeconds.ToString('F1'))s" -ForegroundColor Cyan

# Step 4.5: Fix missing dependencies (jaraco.text)
Write-Host "`n[4.5/5] Fixing missing dependencies..." -ForegroundColor Yellow
$jaracoSrc = ".venv\Lib\site-packages\setuptools\_vendor\jaraco\text\Lorem ipsum.txt"
$jaracoDstDir = "dist\A8轻语\_internal\setuptools\_vendor\jaraco\text"

if (Test-Path $jaracoSrc) {
    if (-not (Test-Path $jaracoDstDir)) {
        New-Item -ItemType Directory -Force -Path $jaracoDstDir | Out-Null
    }
    Copy-Item -Path $jaracoSrc -Destination "$jaracoDstDir\Lorem ipsum.txt" -Force
    Write-Host "Fixed: Copied Lorem ipsum.txt to _internal" -ForegroundColor Green
}
else {
    Write-Host "WARNING: Could not find dependency source: $jaracoSrc" -ForegroundColor Red
}

# Step 5: Copy models directory
Write-Host "`n[5/5] Creating models directory..." -ForegroundColor Yellow
if (-not (Test-Path "dist\A8轻语\models")) {
    New-Item -ItemType Directory -Force -Path "dist\A8轻语\models" | Out-Null
    Write-Host "Created 'models' directory." -ForegroundColor Green
}
else {
    Write-Host "'models' directory already exists." -ForegroundColor Gray
}
Write-Host "NOTE: You must manually copy your models to dist\A8轻语\models" -ForegroundColor Cyan

# Step 6: Clean up for release (remove models from _internal)
Write-Host "`n[6/6] Cleaning up for release..." -ForegroundColor Yellow
$internalModels = "dist\A8轻语\_internal\models"
if (Test-Path $internalModels) {
    # 清空 models 目录内容但保留目录本身
    Get-ChildItem -Path $internalModels -Recurse | Remove-Item -Force -Recurse
    Write-Host "Cleared models content from _internal (keeping empty directory for release)" -ForegroundColor Green
}
else {
    # 创建空的 models 目录
    New-Item -ItemType Directory -Force -Path $internalModels | Out-Null
    Write-Host "Created empty models directory in _internal" -ForegroundColor Green
}

if (Test-Path "dist/A8轻语/A8轻语.exe") {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "  Output: dist/A8轻语/A8轻语.exe" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    Write-Host "`nReady to distribute! Size check:" -ForegroundColor Cyan
    try {
        $size = (Get-Item "dist/A8轻语/A8轻语.exe").Length / 1MB
        Write-Host "EXE Size: $("{0:N2}" -f $size) MB" -ForegroundColor Magenta
    }
    catch {
        Write-Host "Could not determine size."
    }
    
    Write-Host "`nTips for faster builds:" -ForegroundColor Yellow
    Write-Host "  - Use '.\build.ps1 -SkipFrontend' if frontend unchanged" -ForegroundColor Gray
    Write-Host "  - Use '.\build.ps1 -Clean' only when dependencies change" -ForegroundColor Gray
    
    # 显式成功退出
    exit 0
}
else {
    Write-Host "`nBuild failed. Check errors above." -ForegroundColor Red
    # 显式失败退出
    exit 1
}
