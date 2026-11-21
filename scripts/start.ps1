# Start script (single-port demo mode at http://127.0.0.1:8000)
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

Write-Host "==> Building frontend for production..."
Push-Location "frontend"
npm run build
Pop-Location

Write-Host "==> Starting single-port server at http://127.0.0.1:8000..."
Push-Location "backend"
& ".\.venv\Scripts\python.exe" -m uvicorn api.main:app --host 127.0.0.1 --port 8000
Pop-Location
