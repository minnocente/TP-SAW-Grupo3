#!/usr/bin/env bash
# Inicia la app del laboratorio OrderFlow (Linux / macOS)
set -e

if [ ! -x "./.venv/bin/python" ]; then
  echo "No se encontro el entorno virtual. Ejecuta primero  ./setup.sh" >&2
  exit 1
fi

export FLASK_APP=app
export LAB_DEBUG=1

echo "OrderFlow corriendo en http://127.0.0.1:5000  (Ctrl+C para detener)"
./.venv/bin/python -m flask run --host 127.0.0.1 --port 5000 --debug
