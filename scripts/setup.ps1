# Setup script for Vela Compiler and Vela Studio (Windows PowerShell)
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

Write-Host "==> Setting up Python virtual environment..."
if (-not (Test-Path "backend\.venv")) {
    python -m venv "backend\.venv"
}

Write-Host "==> Installing backend dependencies..."
& "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "backend\.venv\Scripts\python.exe" -m pip install -e "backend[dev]"
& "backend\.venv\Scripts\python.exe" -m pip freeze > "backend\requirements.lock"

Write-Host "==> Installing frontend dependencies..."
if (Test-Path "frontend\package.json") {
    Push-Location "frontend"
    npm install
    Pop-Location
}

Write-Host "==> Setup completed successfully!"
