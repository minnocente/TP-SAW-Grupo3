-- Esquema del laboratorio OrderFlow (plataforma ficticia de pedidos y logística)
-- Base: SQLite. Se recrea desde cero cada vez (DROP + CREATE) para reproducibilidad.

PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS clients;

PRAGMA foreign_keys = ON;

-- Clientes (empresas) de la plataforma.
CREATE TABLE clients (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    email   TEXT NOT NULL,
    phone   TEXT,
    address TEXT
);

-- Usuarios del sistema. role: 'user' (cliente) o 'admin' (operaciones internas).
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT,
    role          TEXT NOT NULL DEFAULT 'user',
    client_id     INTEGER REFERENCES clients(id)
);

-- Catálogo de productos.
CREATE TABLE products (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    sku   TEXT NOT NULL UNIQUE,
    price REAL NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0
);

-- Pedidos. Cada pedido pertenece a un cliente.
CREATE TABLE orders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id  INTEGER NOT NULL REFERENCES clients(id),
    status     TEXT NOT NULL DEFAULT 'pendiente',
    total      REAL NOT NULL DEFAULT 0,
    notes      TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Renglones de cada pedido.
CREATE TABLE order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty        INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL DEFAULT 0
);

-- Envíos asociados a pedidos.
CREATE TABLE shipments (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    address  TEXT,
    carrier  TEXT,
    tracking TEXT,
    status   TEXT NOT NULL DEFAULT 'preparando'
);

-- Facturas asociadas a pedidos.
CREATE TABLE invoices (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    number     TEXT NOT NULL,
    amount     REAL NOT NULL DEFAULT 0,
    issued_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
