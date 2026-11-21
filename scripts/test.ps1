# Test script for Vela Compiler and Vela Studio
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

Write-Host "==> Running backend tests..."
Push-Location "backend"
& ".\.venv\Scripts\python.exe" -m pytest -q
$pytestExit = $LASTEXITCODE
Pop-Location

if ($pytestExit -ne 0) {
    Write-Error "Backend tests failed with exit code $pytestExit"
    exit $pytestExit
}

Write-Host "==> Checking backend lint (ruff)..."
Push-Location "backend"
& ".\.venv\Scripts\ruff.exe" check .
$ruffExit = $LASTEXITCODE
Pop-Location

if ($ruffExit -ne 0) {
    Write-Error "Ruff lint failed with exit code $ruffExit"
    exit $ruffExit
}

Write-Host "==> Running frontend type check..."
Push-Location "frontend"
npx tsc --noEmit
$tscExit = $LASTEXITCODE
Pop-Location

if ($tscExit -ne 0) {
    Write-Error "Frontend typecheck failed with exit code $tscExit"
    exit $tscExit
}

Write-Host "==> All tests and checks passed!"
