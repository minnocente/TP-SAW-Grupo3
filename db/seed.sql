-- Datos de ejemplo del laboratorio OrderFlow.
-- Los USUARIOS se cargan desde Python (app/db.py -> seed_users) para hashear contraseñas.

-- Clientes (id 1 = operaciones internas; 2..4 = empresas clientes)
INSERT INTO clients (id, name, email, phone, address) VALUES
    (1, 'OrderFlow Operaciones', 'ops@orderflow.local',      '011-4000-0000', 'Depósito Central, Av. Logística 1000'),
    (2, 'Distribuidora Andina S.A.', 'compras@andina.local', '011-4100-1111', 'Av. San Martín 450, CABA'),
    (3, 'Comercial del Plata SRL', 'pedidos@delplata.local', '011-4200-2222', 'Calle Rivadavia 1820, La Plata'),
    (4, 'Importadora Sur SA', 'admin@implsur.local',         '011-4300-3333', 'Ruta 2 km 55, Berazategui');

-- Productos
INSERT INTO products (id, name, sku, price, stock) VALUES
    (1, 'Caja de cartón reforzada 40x40', 'BOX-4040', 320.00, 1500),
    (2, 'Film stretch industrial 500mm',  'FLM-500',  2150.00, 420),
    (3, 'Pallet de madera estándar',       'PAL-STD',  4800.00, 260),
    (4, 'Cinta de embalar 48mm x 100m',    'TAP-48',   180.50, 3200),
    (5, 'Etiquetas térmicas 100x150 (x500)', 'LBL-100150', 2650.00, 540),
    (6, 'Bolsa antiestática A4 (x1000)',   'BAG-A4',   5400.00, 95),
    (7, 'Separador de cartón corrugado',   'SEP-COR',  95.00, 8000),
    (8, 'Precinto de seguridad numerado',  'SEC-NUM',  42.75, 12000);

-- Pedidos (clave para la demo):
--   cliente1 -> client_id 2 : pedidos 1, 2, 7
--   cliente2 -> client_id 3 : pedidos 3, 4, 8   <- objetivos de IDOR / BFLA
--   cliente3 -> client_id 4 : pedidos 5, 6
INSERT INTO orders (id, client_id, status, total, notes, created_at) VALUES
    (1, 2, 'procesando', 16050.00, 'Entregar en horario de mañana',            '2026-09-10 09:12:00'),
    (2, 2, 'enviado',     9360.00, 'Dejar en portería',                        '2026-09-15 14:03:00'),
    (3, 3, 'procesando', 27400.00, 'Pedido prioritario - cuenta corporativa',  '2026-09-18 11:40:00'),
    (4, 3, 'pendiente',   5400.00, 'Confirmar stock antes de facturar',        '2026-09-20 16:25:00'),
    (5, 4, 'entregado',  12840.00, 'Entregado y conforme',                     '2026-09-05 10:00:00'),
    (6, 4, 'procesando',  3630.00, 'Agregar remito duplicado',                 '2026-09-22 08:50:00'),
    (7, 2, 'pendiente',   1920.00, 'Esperando aprobación de crédito',          '2026-09-25 13:15:00'),
    (8, 3, 'enviado',    21000.00, 'Coordinar con depósito de La Plata',       '2026-09-27 17:30:00');

-- Renglones de pedido
INSERT INTO order_items (order_id, product_id, qty, unit_price) VALUES
    (1, 1, 30, 320.00), (1, 4, 20, 180.50), (1, 2, 1, 2150.00),
    (2, 3, 1, 4800.00), (2, 5, 1, 2650.00), (2, 1, 6, 320.00),
    (3, 6, 4, 5400.00), (3, 2, 2, 2150.00), (3, 5, 1, 2650.00),
    (4, 6, 1, 5400.00),
    (5, 3, 2, 4800.00), (5, 1, 10, 320.00),
    (6, 7, 20, 95.00), (6, 8, 40, 42.75),
    (7, 8, 30, 42.75), (7, 7, 7, 95.00),
    (8, 3, 3, 4800.00), (8, 2, 2, 2150.00), (8, 5, 1, 2650.00);

-- Envíos
INSERT INTO shipments (order_id, address, carrier, tracking, status) VALUES
    (2, 'Av. San Martín 450, CABA', 'Andreani', 'ANDR-000002', 'en_transito'),
    (5, 'Ruta 2 km 55, Berazategui', 'OCA', 'OCA-000005', 'entregado'),
    (8, 'Calle Rivadavia 1820, La Plata', 'Correo Argentino', 'CA-000008', 'preparando');

-- Facturas
INSERT INTO invoices (order_id, number, amount, issued_at) VALUES
    (2, 'A-0001-00000123', 9360.00, '2026-09-15 15:00:00'),
    (5, 'A-0001-00000110', 12840.00, '2026-09-05 11:00:00'),
    (8, 'A-0001-00000130', 21000.00, '2026-09-27 18:00:00');
