"""API REST de OrderFlow.

Esta capa es la superficie de ataque del laboratorio. Contiene las cuatro
vulnerabilidades de la cadena, marcadas con comentarios  >>> VULN <<< .
El resto de los endpoints son "de decorado": realistas pero de implementación
mínima, para que la documentación de la API (Paso 1) luzca completa.
"""
from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash

from ..auth import admin_required, login_required
from ..db import get_db, query

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
        "SELECT id, username, password_hash, role, client_id FROM users WHERE username = ?",
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
        " FROM users u JOIN clients c ON c.id = u.client_id WHERE u.id = ?",
        (g.user["id"],),
        one=True,
    )
    return jsonify(row(user))


@bp.put("/profile")
@login_required
def update_profile():
    data = request.get_json(silent=True) or request.form
    full_name = data.get("full_name")
    db = get_db()
    db.execute(
        "UPDATE users SET full_name = ? WHERE id = ?", (full_name, g.user["id"])
    )
    db.commit()
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
        "SELECT id, name, email, phone, address FROM clients WHERE id = ?",
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
        "SELECT id, name, sku, price, stock FROM products WHERE id = ?",
        (product_id,),
        one=True,
    )
    if p is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(row(p))


@bp.get("/products/search")
@login_required
def search_products():
    """Búsqueda de productos por nombre/SKU.

    >>> VULN (Paso 3) - A05 Injection + A10 Mishandling of Exceptional Conditions <<<
    La consulta se arma concatenando el parámetro `q` directamente en el SQL.
    Además, si la consulta falla, se devuelve el mensaje de error y la query
    completa (fuga de estructura interna).
    """
    q = request.args.get("q", "")
    sql = (
        "SELECT id, name, sku, price, stock FROM products "
        f"WHERE name LIKE '%{q}%' OR sku LIKE '%{q}%'"
    )
    try:
        result = get_db().execute(sql).fetchall()
        return jsonify(rows(result))
    except Exception as exc:  # noqa: BLE001  (fuga intencional de errores)
        return jsonify({"error": str(exc), "query": sql}), 500


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
        " FROM orders WHERE client_id = ? ORDER BY id",
        (g.user["client_id"],),
    )
    return jsonify(rows(result))


@bp.get("/orders/<int:order_id>")
@login_required
def get_order(order_id):
    """Detalle de un pedido.

    >>> VULN (Paso 2) - A01 Broken Access Control / IDOR <<<
    Sólo se exige estar autenticado; NO se verifica que el pedido pertenezca
    al cliente del usuario. Cambiando el id se accede a pedidos ajenos.
    """
    order = query(
        "SELECT id, client_id, status, total, notes, created_at FROM orders WHERE id = ?",
        (order_id,),
        one=True,
    )
    if order is None:
        return jsonify({"error": "Pedido no encontrado"}), 404

    items = query(
        "SELECT oi.id, oi.product_id, p.name AS product_name, oi.qty, oi.unit_price"
        " FROM order_items oi JOIN products p ON p.id = oi.product_id"
        " WHERE oi.order_id = ?",
        (order_id,),
    )
    shipment = query("SELECT * FROM shipments WHERE order_id = ?", (order_id,), one=True)
    invoice = query("SELECT * FROM invoices WHERE order_id = ?", (order_id,), one=True)

    data = row(order)
    data["items"] = rows(items)
    data["shipment"] = row(shipment)
    data["invoice"] = row(invoice)
    return jsonify(data)


@bp.get("/orders/<int:order_id>/items")
@login_required
def get_order_items(order_id):
    # Mismo recurso que el detalle: parte de la superficie del IDOR (Paso 2).
    items = query(
        "SELECT id, order_id, product_id, qty, unit_price FROM order_items WHERE order_id = ?",
        (order_id,),
    )
    return jsonify(rows(items))


@bp.post("/orders")
@login_required
def create_order():
    data = request.get_json(silent=True) or request.form
    notes = data.get("notes", "")
    db = get_db()
    cur = db.execute(
        "INSERT INTO orders (client_id, status, total, notes) VALUES (?, 'pendiente', 0, ?)",
        (g.user["client_id"], notes),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "status": "pendiente"}), 201


@bp.get("/orders/search")
@login_required
def search_orders():
    # Búsqueda parametrizada y acotada al propio cliente (comportamiento correcto).
    status = request.args.get("status", "")
    result = query(
        "SELECT id, client_id, status, total, notes, created_at"
        " FROM orders WHERE client_id = ? AND status LIKE ? ORDER BY id",
        (g.user["client_id"], f"%{status}%"),
    )
    return jsonify(rows(result))


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
        " WHERE s.id = ?",
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
        " WHERE i.id = ?",
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
    db = get_db()
    return jsonify(
        {
            "clients": db.execute("SELECT COUNT(*) AS n FROM clients").fetchone()["n"],
            "orders": db.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"],
            "products": db.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"],
        }
    )


@bp.post("/admin/orders/<int:order_id>")
@login_required  # >>> VULN (Paso 4) - A01 Broken Function Level Authorization <<<
def admin_update_order(order_id):
    """Actualiza un pedido (estado / notas / total).

    Esta función es de administración, pero sólo usa `login_required` en vez de
    `admin_required`: NO verifica el rol. Un usuario común puede invocarla para
    modificar pedidos de cualquier cliente. Es el objetivo final de la cadena.
    """
    order = query("SELECT id FROM orders WHERE id = ?", (order_id,), one=True)
    if order is None:
        return jsonify({"error": "Pedido no encontrado"}), 404

    data = request.get_json(silent=True) or request.form
    fields, params = [], []
    for col in ("status", "notes", "total"):
        if col in data:
            fields.append(f"{col} = ?")
            params.append(data.get(col))
    if not fields:
        return jsonify({"error": "Nada para actualizar"}), 400

    params.append(order_id)
    db = get_db()
    db.execute(f"UPDATE orders SET {', '.join(fields)} WHERE id = ?", params)
    db.commit()
    updated = query(
        "SELECT id, client_id, status, total, notes FROM orders WHERE id = ?",
        (order_id,),
        one=True,
    )
    return jsonify({"status": "pedido actualizado", "order": row(updated)})
