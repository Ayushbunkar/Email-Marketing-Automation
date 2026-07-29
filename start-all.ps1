<#
.SYNOPSIS
    Starts ALL Hermes Email Marketing components with a single command.
.DESCRIPTION
    This script starts the frontend dev server, backend API server, and optionally
    the Celery worker and beat scheduler. Everything runs concurrently.
.NOTES
    Usage: powershell -ExecutionPolicy Bypass -File start-all.ps1
#>

Set-ExecutionPolicy Bypass -Scope Process -Force
$ErrorActionPreference = "SilentlyContinue"

function Write-ColorMessage {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

$Python = "C:\Users\Rupesh\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"

Write-ColorMessage "" ""
Write-ColorMessage "=========================================" "Magenta"
Write-ColorMessage "  Hermes Email Marketing Agent" "Magenta"
Write-ColorMessage "  Starting ALL Components..." "Magenta"
Write-ColorMessage "=========================================" "Magenta"
Write-ColorMessage "" ""

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}
Set-Location $ProjectRoot



$FrontendPath = Join-Path $ProjectRoot "frontend\hermes-frontend"
$NodeModules = Join-Path $FrontendPath "node_modules"

if (-not (Test-Path $NodeModules)) {
    Write-ColorMessage "[*] Installing frontend dependencies..." "Cyan"
    Push-Location $FrontendPath
    cmd /c "npm install"
    Pop-Location
    Write-ColorMessage "[OK] Frontend dependencies installed" "Green"
}

if (Test-Path $NodeModules) {
    Write-ColorMessage "[OK] Frontend dependencies already installed" "Green"
}

Write-ColorMessage "" ""
Write-ColorMessage "[*] Starting all services..." "Cyan"
Write-ColorMessage "" ""

$FrontendCmd = "cd frontend/hermes-frontend && npm run dev"
$BackendCmd = "$Python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Write-ColorMessage "[*] Frontend: http://localhost:5173" "White"
Write-ColorMessage "[*] Backend:  http://localhost:8000" "White"
Write-ColorMessage "[*] API Docs: http://localhost:8000/docs" "White"
Write-ColorMessage "" ""
Write-ColorMessage "Press Ctrl+C to stop all services" "Yellow"
Write-ColorMessage "=========================================" "Magenta"
Write-ColorMessage "" ""

npx concurrently --kill-others --names "FRONTEND,BACKEND" --prefix-colors "blue,green" "$FrontendCmd" "$BackendCmd"
