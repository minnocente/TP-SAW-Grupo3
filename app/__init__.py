"""Application factory del laboratorio TP SAW Grupo 3.

Plataforma ficticia de gestión de pedidos y logística (OrderFlow) usada como
laboratorio de seguridad. Contiene vulnerabilidades sembradas a propósito.
"""
import os

from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from . import auth, db
from .config import Config


SWAGGER_URL = "/api/docs"          # Paso 1 (A02): docs accesibles sin auth
OPENAPI_URL = "/static/openapi.json"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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

    # Crea la base automáticamente si todavía no existe.
    with app.app_context():
        if not os.path.exists(app.config["DATABASE"]):
            db.init_db()

    return app
