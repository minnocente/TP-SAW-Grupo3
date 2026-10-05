"""Acceso a la base PostgreSQL (psycopg2) y utilidades de inicialización."""
import psycopg2
import psycopg2.extras
from flask import current_app, g
from werkzeug.security import generate_password_hash


# Usuarios del laboratorio. Las contraseñas se hashean al sembrar la base.
# (Se documentan en Documentacion/CREDENCIALES.md)
SEED_USERS = [
    # username,  password,     full_name,                   role,    client_id
    ("admin",    "admin123",   "Administrador OrderFlow",   "admin", 1),
    ("nico",     "nico123",    "Nicolás (atacante)",        "user",  89),   # atacante
    ("clopez",   "cliente123", "Carlos Lopez (víctima)",    "user",  458),  # víctima
]


def _connect(dbname=None):
    """Abre una conexión psycopg2 con filas tipo dict."""
    cfg = current_app.config
    return psycopg2.connect(
        host=cfg["DB_HOST"],
        port=cfg["DB_PORT"],
        dbname=dbname or cfg["DB_NAME"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def get_db():
    """Devuelve la conexión PostgreSQL asociada al request actual."""
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), one=False):
    """Helper de consulta con parámetros (uso seguro, placeholders %s)."""
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def execute(sql, params=(), returning=False):
    """Ejecuta una sentencia de escritura y hace commit.

    Si `returning` es True, devuelve la primera fila del RETURNING.
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
        result = cur.fetchone() if returning else None
    db.commit()
    return result


def init_db():
    """Crea el esquema y carga los datos de ejemplo (idempotente)."""
    conn = _connect()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            with open(current_app.config["SCHEMA_SQL"], "r", encoding="utf-8") as f:
                cur.execute(f.read())
            with open(current_app.config["SEED_SQL"], "r", encoding="utf-8") as f:
                cur.execute(f.read())

            # Usuarios con contraseña hasheada (no se pueden hashear desde SQL).
            cur.executemany(
                "INSERT INTO users (username, password_hash, full_name, role, client_id)"
                " VALUES (%s, %s, %s, %s, %s)",
                [
                    (u, generate_password_hash(pw), name, role, cid)
                    for (u, pw, name, role, cid) in SEED_USERS
                ],
            )

            # Reiniciar las secuencias de las tablas con ids explícitos en el seed.
            for table in ("clients", "products", "orders", "order_items",
                          "shipments", "invoices", "transacciones", "users"):
                cur.execute(
                    "SELECT setval(pg_get_serial_sequence(%s, 'id'),"
                    " COALESCE((SELECT MAX(id) FROM {} ), 1), true)".format(table),
                    (table,),
                )
    finally:
        conn.close()


def schema_ready():
    """True si el esquema ya está creado (existe la tabla users)."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.users') AS t")
            return cur.fetchone()["t"] is not None
    finally:
        conn.close()


def init_app(app):
    """Registra el cierre de conexión al finalizar cada request."""
    app.teardown_appcontext(close_db)
