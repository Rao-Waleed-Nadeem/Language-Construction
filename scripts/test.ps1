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

Write-Host "==> Running frontend tests (vitest)..."
Push-Location "frontend"
npm test -- --run
$vitestExit = $LASTEXITCODE
Pop-Location

if ($vitestExit -ne 0) {
    Write-Error "Frontend tests failed with exit code $vitestExit"
    exit $vitestExit
}

Write-Host "==> Running frontend type check & production build..."
Push-Location "frontend"
npm run build
$buildExit = $LASTEXITCODE
Pop-Location

if ($buildExit -ne 0) {
    Write-Error "Frontend build failed with exit code $buildExit"
    exit $buildExit
}

Write-Host "==> All tests, checks, and builds passed successfully!"
