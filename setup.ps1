# Setup del laboratorio OrderFlow (Windows / PowerShell)
# Crea el entorno virtual, instala dependencias e inicializa la base de datos.
$ErrorActionPreference = "Stop"

Write-Host "== OrderFlow lab :: setup ==" -ForegroundColor Cyan

# Verificar Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
  Write-Host "ERROR: Python 3 no esta instalado. Instalalo desde https://www.python.org/downloads/ (marca 'Add to PATH')." -ForegroundColor Red
  exit 1
}

# Crear entorno virtual
if (-not (Test-Path ".venv")) {
  Write-Host "Creando entorno virtual (.venv)..."
  & $python.Source -m venv .venv
}

$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Instalando dependencias..."
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt

Write-Host "Inicializando base de datos..."
& $venvPy scripts\reset_db.py

Write-Host ""
Write-Host "Listo. Ejecuta  .\run.ps1  para iniciar la app en http://127.0.0.1:5000" -ForegroundColor Green
