"""Acceso a la base SQLite (stdlib sqlite3) y utilidades de inicialización."""
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash


# Usuarios del laboratorio. Las contraseñas se hashean al sembrar la base.
# (Se documentan en Documentacion/CREDENCIALES.md)
SEED_USERS = [
    # username,   password,      full_name,              role,    client_id
    ("admin",    "admin123",    "Administrador OrderFlow", "admin", 1),
    ("cliente1", "cliente123",  "Juan Pérez (Andina)",     "user",  2),
    ("cliente2", "cliente123",  "Marta Gómez (del Plata)", "user",  3),
    ("cliente3", "cliente123",  "Luis Sosa (Impl. Sur)",   "user",  4),
]


def get_db():
    """Devuelve la conexión SQLite asociada al request actual."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), one=False):
    """Helper de consulta con parámetros (uso seguro)."""
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def init_db():
    """Crea el esquema y carga los datos de ejemplo (idempotente)."""
    db_path = current_app.config["DATABASE"]
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    with open(current_app.config["SCHEMA_SQL"], "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    with open(current_app.config["SEED_SQL"], "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # Usuarios con contraseña hasheada (no se pueden hashear desde SQL).
    conn.executemany(
        "INSERT INTO users (username, password_hash, full_name, role, client_id)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (u, generate_password_hash(pw), name, role, cid)
            for (u, pw, name, role, cid) in SEED_USERS
        ],
    )

    conn.commit()
    conn.close()


def init_app(app):
    """Registra el cierre de conexión al finalizar cada request."""
    app.teardown_appcontext(close_db)
