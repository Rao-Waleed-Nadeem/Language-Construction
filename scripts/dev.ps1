# Dev script (Vite on 5173 + FastAPI on 8000)
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

Write-Host "==> Starting backend dev server (port 8000)..."
$backendJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location (Join-Path $root "backend")
    & ".\.venv\Scripts\python.exe" -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
} -ArgumentList $ProjectRoot

Write-Host "==> Starting frontend dev server (port 5173)..."
Push-Location "frontend"
npm run dev
Pop-Location

Stop-Job $backendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob -ErrorAction SilentlyContinue
