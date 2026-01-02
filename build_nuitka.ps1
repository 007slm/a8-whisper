# A8轻语 Nuitka Build Script
# Usage: .\build_nuitka.ps1 [-Clean] [-SkipFrontend] [-OneFile]

param(
    [switch]$Clean,
    [switch]$SkipFrontend,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  A8轻语 Nuitka Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Install/Sync Dependencies
Write-Host "`n[1/4] Checking Dependencies..." -ForegroundColor Yellow
cmd /c "uv sync"

# 2. Build Frontend
if (-not $SkipFrontend) {
    Write-Host "`n[2/4] Building Frontend..." -ForegroundColor Yellow
    Push-Location gui_web
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        cmd /c "pnpm install --prefer-offline && pnpm build"
    }
    else {
        cmd /c "npm install && npm run build"
    }
    Pop-Location
}
else {
    Write-Host "`n[2/4] Skipping Frontend Build" -ForegroundColor Gray
}

# 3. Prepare Nuitka Command
Write-Host "`n[3/4] Compiling with Nuitka..." -ForegroundColor Yellow

$outputDir = "dist_nuitka"
if ($Clean) {
    if (Test-Path $outputDir) { Remove-Item -Recurse -Force $outputDir }
}

# Basic Nuitka Arguments
$nuitkaArgs = @(
    "--standalone",
    "--enable-plugin=pyside6",
    "--enable-plugin=numpy",
    "--include-data-dir=src/assets=src/assets",
    "--include-data-dir=gui_web/dist=gui_web/dist",
    "--windows-icon-from-ico=src/assets/icon.ico",
    "--output-dir=$outputDir",
    # Crucial for AI Libraries: Force include all data/dlls in these packages
    "--include-package-data=faster_whisper",
    "--include-package-data=ctranslate2",
    # Fix for jaraco/setuptools hidden dependencies if needed
    "--include-package-data=jaraco", 
    "--jobs=16",
    "--assume-yes-for-downloads", # 自动下载依赖
    # 排除不需要的测试模块，加快编译
    "--nofollow-import-to=numpy.testing",
    "--nofollow-import-to=numpy.distutils", 
    "--nofollow-import-to=numpy.f2py",
    "--nofollow-import-to=pytest",
    "--nofollow-import-to=unittest",
    "--nofollow-import-to=IPython",
    "--nofollow-import-to=matplotlib"
)

if ($OneFile) {
    $nuitkaArgs += "--onefile"
    Write-Host "Mode: OneFile (Single EXE)" -ForegroundColor Magenta
}
else {
    Write-Host "Mode: Standalone (Directory)" -ForegroundColor Magenta
}

# Disable console for release, enable for debugging if needed
# $nuitkaArgs += "--windows-console-mode=disable" 
$nuitkaArgs += "--windows-console-mode=force" # Keep console for now to see logs!

$mainScript = "src/main_webview.py"

Write-Host "Running Nuitka..." -ForegroundColor Cyan
$cmdLine = "uv run python -m nuitka $nuitkaArgs $mainScript"
Write-Host $cmdLine -ForegroundColor DarkGray

cmd /c $cmdLine

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[4/4] Build Success!" -ForegroundColor Green
    if ($OneFile) {
        Write-Host "Output: $outputDir/main_webview.exe" -ForegroundColor Green
    }
    else {
        Write-Host "Output: $outputDir/main_webview.dist/main_webview.exe" -ForegroundColor Green
        
        # Step 4.5: Copy Models (Models are too big to bundle inside EXE usually)
        $distDir = "$outputDir/main_webview.dist"
        if (-not (Test-Path "$distDir/models")) {
            New-Item -ItemType Directory -Force -Path "$distDir/models" | Out-Null
        }
        Write-Host "NOTE: Please copy your 'models' folder to '$distDir/models'" -ForegroundColor Cyan
    }
}
else {
    Write-Host "`nBuild Failed!" -ForegroundColor Red
    exit 1
}
