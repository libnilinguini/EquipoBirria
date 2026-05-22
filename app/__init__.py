"""
Fábrica de la aplicación Flask – SGCI
Equipo Birria
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para acceder a esta página."
login_manager.login_message_category = "warning"


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.controllers.auth_controller         import auth_bp
    from app.controllers.admin_controller        import admin_bp
    from app.controllers.cursos_controller       import cursos_bp
    from app.controllers.materiales_controller   import materiales_bp
    from app.controllers.inscripciones_controller import inscripciones_bp
    from app.controllers.tareas_controller       import tareas_bp

    app.register_blueprint(auth_bp,          url_prefix="/auth")
    app.register_blueprint(admin_bp,         url_prefix="/admin")
    app.register_blueprint(cursos_bp,        url_prefix="/cursos")
    app.register_blueprint(materiales_bp,    url_prefix="/materiales")
    app.register_blueprint(inscripciones_bp, url_prefix="/inscripciones")
    app.register_blueprint(tareas_bp,        url_prefix="/tareas")

    from flask import redirect, url_for, render_template
    from datetime import datetime

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app
