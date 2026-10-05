#!/usr/bin/env bash
# Setup del laboratorio OrderFlow (Linux / macOS) -- PostgreSQL
set -e

echo "== OrderFlow lab :: setup =="

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python 3 no esta instalado." >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "ERROR: PostgreSQL (psql) no esta instalado." >&2
  echo "       En Debian/Ubuntu/Mint:  sudo apt install postgresql" >&2
  exit 1
fi

# Provisiona rol + base si no existen (requiere el superusuario 'postgres').
# El archivo se pasa por stdin para que lo lea TU usuario (el proceso 'postgres'
# no tiene permiso para entrar a tu carpeta home).
echo "Provisionando base PostgreSQL (rol orderflow / base orderflow_lab)..."
if command -v sudo >/dev/null 2>&1; then
  sudo -u postgres psql -v ON_ERROR_STOP=1 < db/create_db.sql
else
  psql -U postgres -v ON_ERROR_STOP=1 < db/create_db.sql
fi

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual (.venv)..."
  python3 -m venv .venv
fi

./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

echo "Inicializando base de datos (esquema + datos de ejemplo)..."
./.venv/bin/python scripts/reset_db.py

echo ""
echo "Listo. Ejecuta  ./run.sh  para iniciar la app en http://127.0.0.1:5000"
