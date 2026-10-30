"""Application factory del laboratorio TP SAW Grupo 3.

Plataforma ficticia de gestión de pedidos y logística (OrderFlow) usada como
laboratorio de seguridad. Contiene vulnerabilidades sembradas a propósito.
"""
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify, render_template, request
from flask.json.provider import DefaultJSONProvider
from flask_swagger_ui import get_swaggerui_blueprint

from . import auth, db
from .config import Config


SWAGGER_URL = "/api/docs"          # Paso 1 (A02): docs accesibles sin auth
OPENAPI_URL = "/static/openapi.json"


class LabJSONProvider(DefaultJSONProvider):
    """Serializa los tipos de PostgreSQL (Decimal, date) que devuelve psycopg2."""

    sort_keys = False

    @staticmethod
    def default(o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return DefaultJSONProvider.default(o)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json = LabJSONProvider(app)

    # Infra
    db.init_app(app)
    auth.init_app(app)

    # Blueprints de la aplicación
    from .routes.web import bp as web_bp
    from .routes.api import bp as api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    # Swagger UI (interactivo). Expuesto públicamente -> Security Misconfiguration.
    swagger_bp = get_swaggerui_blueprint(
        SWAGGER_URL,
        OPENAPI_URL,
        config={"app_name": "OrderFlow API"},
    )
    app.register_blueprint(swagger_bp, url_prefix=SWAGGER_URL)

    # Páginas de error de la fachada. Las rutas de la API devuelven su propio
    # JSON de error de forma explícita, así que este handler sólo alcanza a las
    # rutas no encontradas: responde JSON bajo /api/ y una página con la estética
    # del portal en el resto.
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Recurso no encontrado"}), 404
        return render_template("404.html"), 404

    # Crea el esquema automáticamente si todavía no existe.
    with app.app_context():
        try:
            if not db.schema_ready():
                db.init_db()
        except Exception as exc:  # noqa: BLE001
            app.logger.warning("No se pudo inicializar la base: %s", exc)

    return app
