<#
Start backend FastAPI server in the project root using the virtualenv.

Usage (PowerShell):
  .\run_backend.ps1 [-Port 8000]

This activates the venv, ensures the current directory is the project root,
and runs uvicorn with the module path `backend.main:app` so Python can import
the `backend` package.
#>
param(
    [int]$Port = 8000
)

Write-Host "Starting backend on port $Port..."

if (-not (Test-Path -Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Error ".venv not found. Activate your virtualenv first or create one at ./.venv"
    exit 1
}

# Activate virtualenv
& ".\.venv\Scripts\Activate.ps1"

# Ensure we run uvicorn from project root so `backend` is importable
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# If uvicorn is installed in the venv, call it via -m to use the venv's interpreter
& "${env:VIRTUAL_ENV}\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port $Port
