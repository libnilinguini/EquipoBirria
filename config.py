"""
Configuración del Sistema de Gestión de Cursos de Idiomas (SGCI)
Equipo Birria
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuración base compartida por todos los entornos."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "sgci-equipo-birria-dev-key-cambiar-en-produccion")

    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'sgci.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Subida de archivos (Materiales)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB máximo
    ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "mp4", "png", "jpg", "jpeg"}


class DevelopmentConfig(Config):
    """Configuración para desarrollo local."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Configuración para pruebas unitarias (compatible con test_*.py del equipo)."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configuración para producción."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
