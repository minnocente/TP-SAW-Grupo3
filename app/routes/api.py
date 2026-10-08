"""API REST de OrderFlow.

Esta capa es la superficie de ataque del laboratorio. Contiene las
vulnerabilidades de la cadena, marcadas con comentarios  >>> VULN <<< .
El resto de los endpoints son "de decorado": realistas pero de implementación
mínima, para que la documentación de la API (Paso 1) luzca completa.

Cadena (cada paso depende del anterior):
    Paso 1  A02  /api/docs expuesto  ->  revela los endpoints legacy (sin filtrar valores).
    Paso 2  A01  GET /api/v1/pedidos/<id>/comprobante  (IDOR): ÚNICA fuente del cliente_id
                 de la víctima (458) y de una `factura_referencia` válida (token opaco).
    Paso 3  A10  GET /api/v1/facturas/ver?ref=...': filtro bypassable + fuga de error que
                 revela la tabla/columnas internas (ldg_fin_legacy: acct_no, pay_raw...).
    Paso 4  A05  idem (SQLi por concatenación) + A04 (tarjetas en texto plano): el payload
                 acotado a la víctima (OR acct_no=458) necesita el id (Paso 2) y el nombre
                 de columna (Paso 3); sin ambos no se puede llegar hasta acá.
"""
import re

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash

from ..auth import admin_required, login_required
from ..db import execute, get_db, query

bp = Blueprint("api", __name__, url_prefix="/api")


def rows(result):
    return [dict(r) for r in result]


def row(result):
    return dict(result) if result is not None else None


# --------------------------------------------------------------------------- #
# Meta (sin autenticación)
# --------------------------------------------------------------------------- #
@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.get("/version")
def version():
    return jsonify({"name": "OrderFlow API", "version": "1.4.2", "env": "lab"})


# --------------------------------------------------------------------------- #
# Autenticación / perfil
# --------------------------------------------------------------------------- #
@bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    # Consulta parametrizada: el login NO es inyectable.
    user = query(
        "SELECT id, username, password_hash, role, client_id FROM users WHERE username = %s",
        (username,),
        one=True,
    )
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Credenciales inválidas"}), 401
    session.clear()
    session["user_id"] = user["id"]
    return jsonify(
        {"id": user["id"], "username": user["username"], "role": user["role"]}
    )


@bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"status": "sesión cerrada"})


@bp.get("/auth/me")
@login_required
def me():
    return jsonify(row(g.user))


@bp.get("/profile")
@login_required
def get_profile():
    user = query(
        "SELECT u.id, u.username, u.full_name, u.role, u.client_id,"
        " c.name AS client_name, c.email AS client_email"
        " FROM users u JOIN clients c ON c.id = u.client_id WHERE u.id = %s",
        (g.user["id"],),
        one=True,
    )
    return jsonify(row(user))


@bp.put("/profile")
@login_required
def update_profile():
    data = request.get_json(silent=True) or request.form
    full_name = data.get("full_name")
    execute("UPDATE users SET full_name = %s WHERE id = %s", (full_name, g.user["id"]))
    return jsonify({"status": "perfil actualizado"})


# --------------------------------------------------------------------------- #
# Clientes
# --------------------------------------------------------------------------- #
@bp.get("/clients")
@admin_required
def list_clients():
    return jsonify(rows(query("SELECT id, name, email, phone, address FROM clients")))


@bp.get("/clients/<int:client_id>")
@login_required
def get_client(client_id):
    # Un usuario sólo puede ver su propio cliente (salvo admin).
    if g.user["role"] != "admin" and g.user["client_id"] != client_id:
        return jsonify({"error": "No autorizado"}), 403
    c = query(
        "SELECT id, name, email, phone, address FROM clients WHERE id = %s",
        (client_id,),
        one=True,
    )
    if c is None:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify(row(c))


# --------------------------------------------------------------------------- #
# Productos / stock
# --------------------------------------------------------------------------- #
@bp.get("/products")
@login_required
def list_products():
    return jsonify(rows(query("SELECT id, name, sku, price, stock FROM products")))


@bp.get("/products/<int:product_id>")
@login_required
def get_product(product_id):
    p = query(
        "SELECT id, name, sku, price, stock FROM products WHERE id = %s",
        (product_id,),
        one=True,
    )
    if p is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(row(p))


@bp.get("/products/search")
@login_required
def search_products():
    """Búsqueda de productos por nombre/SKU (consulta parametrizada, segura)."""
    q = request.args.get("q", "")
    like = f"%{q}%"
    result = query(
        "SELECT id, name, sku, price, stock FROM products"
        " WHERE name ILIKE %s OR sku ILIKE %s",
        (like, like),
    )
    return jsonify(rows(result))


@bp.get("/stock")
@admin_required
def stock_levels():
    return jsonify(rows(query("SELECT id, name, sku, stock FROM products ORDER BY stock ASC")))


# --------------------------------------------------------------------------- #
# Pedidos
# --------------------------------------------------------------------------- #
@bp.get("/orders")
@login_required
def list_orders():
    """Lista los pedidos del cliente del usuario (comportamiento correcto)."""
    result = query(
        "SELECT id, client_id, status, total, notes, created_at"
        " FROM orders WHERE client_id = %s ORDER BY id",
        (g.user["client_id"],),
    )
    return jsonify(rows(result))


@bp.get("/orders/<int:order_id>")
@login_required
def get_order(order_id):
    """Detalle de un pedido (con validación de propiedad)."""
    order = query(
        "SELECT id, client_id, status, total, notes, created_at FROM orders WHERE id = %s",
        (order_id,),
        one=True,
    )
    if order is None:
        return jsonify({"error": "Pedido no encontrado"}), 404
    if g.user["role"] != "admin" and order["client_id"] != g.user["client_id"]:
        return jsonify({"error": "No autorizado"}), 403

    items = query(
        "SELECT oi.id, oi.product_id, p.name AS product_name, oi.qty, oi.unit_price"
        " FROM order_items oi JOIN products p ON p.id = oi.product_id"
        " WHERE oi.order_id = %s",
        (order_id,),
    )
    shipment = query("SELECT * FROM shipments WHERE order_id = %s", (order_id,), one=True)
    invoice = query("SELECT * FROM invoices WHERE order_id = %s", (order_id,), one=True)

    data = row(order)
    data["items"] = rows(items)
    data["shipment"] = row(shipment)
    data["invoice"] = row(invoice)
    return jsonify(data)


@bp.get("/orders/<int:order_id>/items")
@login_required
def get_order_items(order_id):
    order = query("SELECT client_id FROM orders WHERE id = %s", (order_id,), one=True)
    if order is None:
        return jsonify({"error": "Pedido no encontrado"}), 404
    if g.user["role"] != "admin" and order["client_id"] != g.user["client_id"]:
        return jsonify({"error": "No autorizado"}), 403
    items = query(
        "SELECT id, order_id, product_id, qty, unit_price FROM order_items WHERE order_id = %s",
        (order_id,),
    )
    return jsonify(rows(items))


@bp.post("/orders")
@login_required
def create_order():
    data = request.get_json(silent=True) or request.form
    notes = data.get("notes", "")
    new = execute(
        "INSERT INTO orders (client_id, status, total, notes)"
        " VALUES (%s, 'pendiente', 0, %s) RETURNING id",
        (g.user["client_id"], notes),
        returning=True,
    )
    return jsonify({"id": new["id"], "status": "pendiente"}), 201


@bp.get("/orders/search")
@login_required
def search_orders():
    # Búsqueda parametrizada y acotada al propio cliente (comportamiento correcto).
    status = request.args.get("status", "")
    result = query(
        "SELECT id, client_id, status, total, notes, created_at"
        " FROM orders WHERE client_id = %s AND status ILIKE %s ORDER BY id",
        (g.user["client_id"], f"%{status}%"),
    )
    return jsonify(rows(result))


# --------------------------------------------------------------------------- #
# Pedidos v1 (API legacy de reportes)
# --------------------------------------------------------------------------- #
@bp.get("/v1/pedidos/<int:pedido_id>/comprobante")
@login_required
def comprobante(pedido_id):
    """Comprobante de un pedido (endpoint legacy de reportes).

    >>> VULN (Paso 2) - A01 Broken Access Control / IDOR <<<
    Sólo exige estar autenticado; NO verifica que el pedido pertenezca al
    cliente del usuario. Probando ids correlativos se accede a comprobantes
    ajenos. Es la ÚNICA fuente del `cliente_id` de la víctima (458) y de una
    `factura_referencia` válida (token opaco, no adivinable): sin este paso no
    se puede armar el payload acotado de los Pasos 3 y 4.
    """
    o = query(
        "SELECT id, client_id, total, factura_referencia, created_at"
        " FROM orders WHERE id = %s",
        (pedido_id,),
        one=True,
    )
    if o is None:
        return jsonify({"error": "Comprobante no encontrado"}), 404
    fecha = o["created_at"].date() if o["created_at"] is not None else None
    return jsonify(
        {
            "pedido_id": o["id"],
            "fecha": fecha,
            "cliente_id": o["client_id"],
            "factura_referencia": o["factura_referencia"],
            "total": o["total"],
        }
    )


# --------------------------------------------------------------------------- #
# Facturación v1
# --------------------------------------------------------------------------- #
@bp.get("/v1/facturas/ver")
@login_required
def ver_factura():
    """Consulta de una factura por su referencia.

    >>> VULN (Pasos 3 y 4) - A10 + A05 + A04 <<<
    - A10: hay un filtro de formato con regex, pero `re.match` ancla sólo el
      INICIO del string (sin `$`), así que un payload que empieza con una ref
      de formato válido y concatena SQL igual lo supera. Ante una excepción se
      devuelve el mensaje de error y la query completa: así se filtran la tabla
      interna (`ldg_fin_legacy`) y sus columnas opacas (`acct_no`, `pay_raw`...),
      dato necesario para armar el payload acotado del Paso 4.
    - A05: la consulta se arma CONCATENANDO el parámetro `ref` en el SQL.
    - A04: `pay_raw` guarda tarjetas en texto plano y se devuelven tal cual.
    """
    ref = request.args.get("ref", "")

    # Filtro de formato (bypassable: ancla sólo el inicio).
    if not re.match(r"^FAC-\d{4}-[A-Z0-9]{8}", ref):
        return jsonify({"error": "Formato de referencia inválido"}), 400

    sql = (
        "SELECT id, acct_no, fecha, total, detalle_items, pay_raw "
        f"FROM ldg_fin_legacy WHERE doc_ref = '{ref}'"
    )
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchall()
        return jsonify(rows(result))
    except Exception as exc:  # noqa: BLE001  (fuga intencional de errores)
        db.rollback()
        return jsonify({"error": str(exc), "query": sql}), 500


# --------------------------------------------------------------------------- #
# Envíos
# --------------------------------------------------------------------------- #
@bp.get("/shipments")
@admin_required
def list_shipments():
    return jsonify(rows(query("SELECT * FROM shipments")))


@bp.get("/shipments/<int:shipment_id>")
@login_required
def get_shipment(shipment_id):
    s = query(
        "SELECT s.*, o.client_id FROM shipments s JOIN orders o ON o.id = s.order_id"
        " WHERE s.id = %s",
        (shipment_id,),
        one=True,
    )
    if s is None:
        return jsonify({"error": "Envío no encontrado"}), 404
    if g.user["role"] != "admin" and s["client_id"] != g.user["client_id"]:
        return jsonify({"error": "No autorizado"}), 403
    return jsonify(row(s))


# --------------------------------------------------------------------------- #
# Facturación
# --------------------------------------------------------------------------- #
@bp.get("/invoices")
@admin_required
def list_invoices():
    return jsonify(rows(query("SELECT * FROM invoices")))


@bp.get("/invoices/<int:invoice_id>")
@login_required
def get_invoice(invoice_id):
    inv = query(
        "SELECT i.*, o.client_id FROM invoices i JOIN orders o ON o.id = i.order_id"
        " WHERE i.id = %s",
        (invoice_id,),
        one=True,
    )
    if inv is None:
        return jsonify({"error": "Factura no encontrada"}), 404
    if g.user["role"] != "admin" and inv["client_id"] != g.user["client_id"]:
        return jsonify({"error": "No autorizado"}), 403
    return jsonify(row(inv))


# --------------------------------------------------------------------------- #
# Administración
# --------------------------------------------------------------------------- #
@bp.get("/admin/orders")
@admin_required
def admin_list_orders():
    return jsonify(rows(query("SELECT * FROM orders ORDER BY id")))


@bp.get("/admin/users")
@admin_required
def admin_list_users():
    return jsonify(
        rows(query("SELECT id, username, full_name, role, client_id FROM users"))
    )


@bp.get("/admin/stats")
@admin_required
def admin_stats():
    return jsonify(
        {
            "clients": query("SELECT COUNT(*) AS n FROM clients", one=True)["n"],
            "orders": query("SELECT COUNT(*) AS n FROM orders", one=True)["n"],
            "products": query("SELECT COUNT(*) AS n FROM products", one=True)["n"],
        }
    )


@bp.post("/admin/orders/<int:order_id>")
@admin_required
def admin_update_order(order_id):
    """Actualiza un pedido (estado / notas / total). Requiere rol admin."""
    order = query("SELECT id FROM orders WHERE id = %s", (order_id,), one=True)
    if order is None:
        return jsonify({"error": "Pedido no encontrado"}), 404

    data = request.get_json(silent=True) or request.form
    fields, params = [], []
    for col in ("status", "notes", "total"):
        if col in data:
            fields.append(f"{col} = %s")
            params.append(data.get(col))
    if not fields:
        return jsonify({"error": "Nada para actualizar"}), 400

    params.append(order_id)
    execute(f"UPDATE orders SET {', '.join(fields)} WHERE id = %s", params)
    updated = query(
        "SELECT id, client_id, status, total, notes FROM orders WHERE id = %s",
        (order_id,),
        one=True,
    )
    return jsonify({"status": "pedido actualizado", "order": row(updated)})
