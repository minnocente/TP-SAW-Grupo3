-- Datos de ejemplo del laboratorio OrderFlow.
-- Los USUARIOS se cargan desde Python (app/db.py -> SEED_USERS) para hashear contraseñas.

-- Clientes (empresas)
--   1   = OrderFlow Operaciones (admin interno)
--   89  = empresa del atacante (nico)
--   458 = empresa de la víctima (Carlos Lopez)
INSERT INTO clients (id, name, email, phone, address) VALUES
    (1,   'OrderFlow Operaciones',        'ops@orderflow.local',       '011-4000-0000', 'Depósito Central, Av. Logística 1000'),
    (89,  'Competidora Rápida SRL',       'compras@competidora.local', '011-4100-1111', 'Av. San Martín 450, CABA'),
    (458, 'Comercial Lopez e Hijos S.A.', 'pedidos@lopezsa.local',     '011-4200-2222', 'Calle Rivadavia 1820, La Plata');

-- Catálogo de productos (fachada web).
INSERT INTO products (id, name, sku, price, stock) VALUES
    (1, 'Pallet Cajas Cartón Reforzado 40x40',          'BOX-4040',   60000.00, 1500),
    (2, 'Film Stretch Industrial 500mm',                'FLM-500',    10000.00, 420),
    (3, 'Cinta de Embalaje Transparente x 48mm',        'TAP-48',      3200.00, 3200),
    (4, 'Dispensador de Cinta Manual Reforzado',        'DSP-MAN',    15000.00, 260),
    (5, 'Precintos de Seguridad Plásticos Numerados x 1000', 'SEC-1000', 125000.00, 540),
    (6, 'Etiquetas térmicas 100x150 (x500)',            'LBL-100150',  2650.00, 540),
    (7, 'Separador de cartón corrugado',                'SEP-COR',       95.00, 8000),
    (8, 'Bolsa antiestática A4 (x1000)',                'BAG-A4',      5400.00, 95);

-- Pedidos. `factura_referencia` es la referencia que devuelve el comprobante (Paso 2).
--   nico (client 89) es dueño del pedido 105; al probar hacia atrás llega al 104 (víctima 458).
INSERT INTO orders (id, client_id, status, total, notes, factura_referencia, created_at) VALUES
    (100, 458, 'entregado',  210000.00, 'Entrega en depósito La Plata',        'FAC-2026-00456', '2026-07-15 10:00:00'),
    (101, 458, 'entregado',  310000.00, 'Coordinar con portería',              'FAC-2026-00457', '2026-08-12 09:30:00'),
    (102, 89,  'procesando',  48000.00, 'Entregar en horario de mañana',       'FAC-2026-00087', '2026-08-20 11:10:00'),
    (103, 89,  'enviado',     90000.00, 'Dejar en recepción',                  'FAC-2026-00088', '2026-09-01 14:03:00'),
    (104, 458, 'procesando', 125000.00, 'Pedido prioritario - cuenta corporativa', 'FAC-2026-00458', '2026-09-10 11:40:00'),
    (105, 89,  'pendiente',   72000.00, 'Esperando aprobación de crédito',     'FAC-2026-00089', '2026-09-25 13:15:00');

-- Renglones (sostienen la vista web del detalle de pedido).
INSERT INTO order_items (order_id, product_id, qty, unit_price) VALUES
    (102, 1, 1, 60000.00),
    (103, 2, 9, 10000.00),
    (105, 1, 1, 60000.00), (105, 3, 1, 3200.00);

-- Envíos
INSERT INTO shipments (order_id, address, carrier, tracking, status) VALUES
    (103, 'Av. San Martín 450, CABA', 'Andreani', 'ANDR-000103', 'en_transito'),
    (100, 'Calle Rivadavia 1820, La Plata', 'OCA', 'OCA-000100', 'entregado');

-- Facturas (fachada)
INSERT INTO invoices (order_id, number, amount, issued_at) VALUES
    (103, 'FAC-2026-00088', 90000.00,  '2026-09-01 15:00:00'),
    (100, 'FAC-2026-00456', 210000.00, '2026-07-15 11:00:00');

-- Transacciones financieras (Pasos 3 y 4). `datos_pago` EN TEXTO PLANO (A04 a propósito).
--   Víctima cliente_id=458: ids 88, 95, 104 (historial completo que exfiltra el atacante).
INSERT INTO transacciones (id, cliente_id, fecha, total, detalle_items, datos_pago, ref) VALUES
    (88, 458, '2026-07-15', 450000.00,
     '[{"producto": "Pallet Cajas Cartón Reforzado 40x40", "cantidad": 5, "precio_unitario": 60000.00}, {"producto": "Film Stretch Industrial 500mm", "cantidad": 15, "precio_unitario": 10000.00}]'::jsonb,
     'PAN: 4509-8812-3456-8921 | VENC: 11/28 | CVV: 732 | TITULAR: CARLOS LOPEZ',
     'FAC-2026-00456'),
    (95, 458, '2026-08-12', 310000.00,
     '[{"producto": "Cinta de Embalaje Transparente x 48mm", "cantidad": 50, "precio_unitario": 3200.00}, {"producto": "Dispensador de Cinta Manual Reforzado", "cantidad": 10, "precio_unitario": 15000.00}]'::jsonb,
     'PAN: 4509-8812-3456-8921 | VENC: 11/28 | CVV: 732 | TITULAR: CARLOS LOPEZ',
     'FAC-2026-00457'),
    (104, 458, '2026-09-10', 125000.00,
     '[{"producto": "Precintos de Seguridad Plásticos Numerados x 1000", "cantidad": 1, "precio_unitario": 125000.00}]'::jsonb,
     'PAN: 4509-8812-3456-8921 | VENC: 11/28 | CVV: 732 | TITULAR: CARLOS LOPEZ',
     'FAC-2026-00458'),
    -- Transacción propia del atacante (consulta legítima por su propia ref).
    (112, 89, '2026-09-25', 72000.00,
     '[{"producto": "Pallet Cajas Cartón Reforzado 40x40", "cantidad": 1, "precio_unitario": 60000.00}, {"producto": "Cinta de Embalaje Transparente x 48mm", "cantidad": 1, "precio_unitario": 3200.00}]'::jsonb,
     'PAN: 4000-1234-5678-9010 | VENC: 05/27 | CVV: 111 | TITULAR: NICOLAS COMPETIDOR',
     'FAC-2026-00089'),
    -- Otro cliente, para que el OR cliente_id=458 recorte visiblemente al conjunto de la víctima.
    (120, 1, '2026-09-05', 15000.00,
     '[{"producto": "Etiquetas térmicas 100x150 (x500)", "cantidad": 5, "precio_unitario": 2650.00}]'::jsonb,
     'PAN: 4777-0000-1111-2222 | VENC: 09/26 | CVV: 999 | TITULAR: ORDERFLOW OPS',
     'FAC-2026-00001');
