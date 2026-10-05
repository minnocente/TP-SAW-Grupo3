"""Configuración de la aplicación del laboratorio.

NOTA DE LABORATORIO: varios valores acá son intencionalmente inseguros
(DEBUG activado, SECRET_KEY fija, credenciales de BD por defecto) para poder
demostrar la cadena de ataque. No usar como referencia de configuración de
producción.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    # SECRET_KEY fija y conocida: suficiente para la maqueta local.
    SECRET_KEY = os.environ.get("SECRET_KEY", "lab-tp-saw-grupo3-clave-demo")

    # Conexión a PostgreSQL. Defaults de laboratorio (ver db/create_db.sql).
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "5432"))
    DB_NAME = os.environ.get("DB_NAME", "orderflow_lab")
    DB_USER = os.environ.get("DB_USER", "orderflow")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "orderflow")

    # A02 - Security Misconfiguration: DEBUG expone errores verbosos.
    DEBUG = os.environ.get("LAB_DEBUG", "1") == "1"

    # Rutas de los SQL de inicialización.
    SCHEMA_SQL = os.path.join(BASE_DIR, "db", "schema.sql")
    SEED_SQL = os.path.join(BASE_DIR, "db", "seed.sql")

    JSON_SORT_KEYS = False
