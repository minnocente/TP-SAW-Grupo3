# Inicia la app del laboratorio OrderFlow (Windows / PowerShell)
$ErrorActionPreference = "Stop"

$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
  Write-Host "No se encontro el entorno virtual. Ejecuta primero  .\setup.ps1" -ForegroundColor Red
  exit 1
}

$env:FLASK_APP = "app"
$env:LAB_DEBUG = "1"

Write-Host "OrderFlow corriendo en http://127.0.0.1:5000  (Ctrl+C para detener)" -ForegroundColor Green
& $venvPy -m flask run --host 127.0.0.1 --port 5000 --debug
