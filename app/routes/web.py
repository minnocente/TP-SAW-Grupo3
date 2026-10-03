"""Vistas web (Jinja) de OrderFlow.

La UI es la fachada de "aplicación normal". No muestra ninguna pista de las
vulnerabilidades: carga sus datos consumiendo la API REST (app/routes/api.py),
que es la superficie de ataque real del laboratorio.
"""
from flask import (
    Blueprint,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from ..auth import login_required
from ..db import query

bp = Blueprint("web", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = query(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,),
            one=True,
        )
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Usuario o contraseña incorrectos."
        else:
            session.clear()
            session["user_id"] = user["id"]
            nxt = request.args.get("next") or url_for("web.dashboard")
            return redirect(nxt)
    return render_template("login.html", error=error)


@bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("web.login"))


@bp.get("/")
@login_required
def dashboard():
    return render_template("dashboard.html")


@bp.get("/orders")
@login_required
def orders():
    return render_template("orders.html")


@bp.get("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    # El template pide los datos a /api/orders/<id> (ahí vive el IDOR).
    return render_template("order_detail.html", order_id=order_id)


@bp.get("/products")
@login_required
def products():
    return render_template("products.html")


@bp.get("/profile")
@login_required
def profile():
    return render_template("profile.html")
