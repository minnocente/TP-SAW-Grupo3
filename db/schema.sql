-- Esquema del laboratorio OrderFlow (plataforma ficticia de pedidos y logística)
-- Base: PostgreSQL. Se recrea desde cero cada vez (DROP + CREATE) para reproducibilidad.

DROP TABLE IF EXISTS transacciones CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS shipments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS clients CASCADE;

-- Clientes (empresas) de la plataforma.
CREATE TABLE clients (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    email   TEXT NOT NULL,
    phone   TEXT,
    address TEXT
);

-- Usuarios del sistema. role: 'user' (cliente) o 'admin' (operaciones internas).
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT,
    role          TEXT NOT NULL DEFAULT 'user',
    client_id     INTEGER REFERENCES clients(id)
);

-- Catálogo de productos.
CREATE TABLE products (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL,
    sku   TEXT NOT NULL UNIQUE,
    price NUMERIC(12,2) NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0
);

-- Pedidos. Cada pedido pertenece a un cliente.
-- `factura_referencia` respalda el comprobante consultado en el Paso 2 (IDOR).
CREATE TABLE orders (
    id                  SERIAL PRIMARY KEY,
    client_id           INTEGER NOT NULL REFERENCES clients(id),
    status              TEXT NOT NULL DEFAULT 'pendiente',
    total               NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes               TEXT,
    factura_referencia  TEXT,
    created_at          TIMESTAMP NOT NULL DEFAULT now()
);

-- Renglones de cada pedido.
CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty        INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0
);

-- Envíos asociados a pedidos.
CREATE TABLE shipments (
    id       SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    address  TEXT,
    carrier  TEXT,
    tracking TEXT,
    status   TEXT NOT NULL DEFAULT 'preparando'
);

-- Facturas asociadas a pedidos.
CREATE TABLE invoices (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    number     TEXT NOT NULL,
    amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
    issued_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- Transacciones financieras (respaldan GET /api/v1/facturas/ver, Pasos 3 y 4).
-- `datos_pago` guarda los datos de tarjeta EN TEXTO PLANO a propósito (A04).
CREATE TABLE transacciones (
    id            SERIAL PRIMARY KEY,
    cliente_id    INTEGER NOT NULL,
    fecha         DATE,
    total         NUMERIC(12,2) NOT NULL DEFAULT 0,
    detalle_items JSONB,
    datos_pago    TEXT,
    ref           TEXT
);
