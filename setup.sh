#!/usr/bin/env bash
# Setup del laboratorio OrderFlow (Linux / macOS)
set -e

echo "== OrderFlow lab :: setup =="

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python 3 no esta instalado." >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual (.venv)..."
  python3 -m venv .venv
fi

./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

echo "Inicializando base de datos..."
./.venv/bin/python scripts/reset_db.py

echo ""
echo "Listo. Ejecuta  ./run.sh  para iniciar la app en http://127.0.0.1:5000"
