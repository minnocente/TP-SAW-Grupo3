"""Reinicia la base del laboratorio (recrea esquema + datos de ejemplo).

Uso:
    python scripts/reset_db.py

Útil para dejar la maqueta en su estado inicial entre demos.
"""
import os
import sys

# Permite ejecutar el script desde la raíz del proyecto.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from app.db import init_db  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        init_db()
        print(f"Base reiniciada en: {app.config['DATABASE']}")


if __name__ == "__main__":
    main()
