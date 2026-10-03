"""Autenticación por sesión y decoradores de autorización.

El decorador `login_required` valida que haya una sesión iniciada.
El decorador `admin_required` valida además el rol de administrador.

NOTA DE LABORATORIO (A01 - Broken Function Level Authorization):
el decorador `admin_required` existe y se usa en casi todos los endpoints
de administración... pero intencionalmente NO se aplica en
`POST /api/admin/orders/<id>` (ver app/routes/api.py). Ese olvido es la
vulnerabilidad del Paso 4 de la cadena.
"""
from functools import wraps

from flask import g, jsonify, redirect, request, session, url_for

from .db import query


def load_logged_in_user():
    """Carga el usuario de la sesión en `g.user` antes de cada request."""
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = query(
            "SELECT id, username, role, client_id FROM users WHERE id = ?",
            (user_id,),
            one=True,
        )


def _wants_json():
    return request.path.startswith("/api/")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            if _wants_json():
                return jsonify({"error": "No autenticado"}), 401
            return redirect(url_for("web.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            if _wants_json():
                return jsonify({"error": "No autenticado"}), 401
            return redirect(url_for("web.login", next=request.path))
        if g.user["role"] != "admin":
            if _wants_json():
                return jsonify({"error": "Requiere rol de administrador"}), 403
            return ("Acceso denegado", 403)
        return view(*args, **kwargs)

    return wrapped


def init_app(app):
    app.before_request(load_logged_in_user)
