"""Configuración de la aplicación del laboratorio.

NOTA DE LABORATORIO: varios valores acá son intencionalmente inseguros
(DEBUG activado, SECRET_KEY fija) para poder demostrar la cadena de ataque.
No usar como referencia de configuración de producción.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    # SECRET_KEY fija y conocida: suficiente para la maqueta local.
    SECRET_KEY = os.environ.get("SECRET_KEY", "lab-tp-saw-grupo3-clave-demo")

    # Base SQLite por archivo (portable, sin servidor).
    DATABASE = os.environ.get(
        "LAB_DATABASE", os.path.join(BASE_DIR, "data", "lab.sqlite")
    )

    # A02 - Security Misconfiguration: DEBUG expone errores verbosos.
    DEBUG = os.environ.get("LAB_DEBUG", "1") == "1"

    # Rutas de los SQL de inicialización.
    SCHEMA_SQL = os.path.join(BASE_DIR, "db", "schema.sql")
    SEED_SQL = os.path.join(BASE_DIR, "db", "seed.sql")

    JSON_SORT_KEYS = False
