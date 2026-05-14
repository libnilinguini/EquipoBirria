"""
run.py – Punto de entrada del SGCI
Equipo Birria

Uso:
    python run.py                   # Inicia en modo desarrollo (por defecto)
    FLASK_ENV=production python run.py

Variables de entorno relevantes:
    FLASK_ENV       → 'development' | 'testing' | 'production'  (default: development)
    SECRET_KEY      → Clave secreta de la app (obligatoria en producción)
    DATABASE_URL    → URI de conexión a la BD   (default: SQLite local)
"""

import os
from app import create_app, db
from app.models.models import Usuario, Curso, Inscripcion, Material, RolUsuario

# Determinar el entorno desde variable de entorno (default: development)
flask_env = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name=flask_env)


# ---------------------------------------------------------------------------
# Shell context: disponible en `flask shell` para pruebas rápidas
# ---------------------------------------------------------------------------

@app.shell_context_processor
def make_shell_context():
    """
    Inyecta objetos útiles en el shell interactivo de Flask.
    Ejecutar con:  flask shell
    """
    return {
        "db": db,
        "Usuario": Usuario,
        "Curso": Curso,
        "Inscripcion": Inscripcion,
        "Material": Material,
    }


# ---------------------------------------------------------------------------
# Comando CLI: inicializar la base de datos
# ---------------------------------------------------------------------------

@app.cli.command("init-db")
def init_db():
    """
    Crea todas las tablas en la base de datos y genera un usuario
    administrador de ejemplo.

    Ejecutar con:  flask init-db
    """
    with app.app_context():
        db.create_all()
        print("✅  Tablas creadas correctamente.")

        # Crear admin por defecto si no existe
        if not Usuario.query.filter_by(email="admin@sgci.com").first():
            admin = Usuario(
                nombre="Admin",
                apellido="SGCI",
                email="admin@sgci.com",
                rol=RolUsuario.ADMINISTRADOR,
            )
            admin.set_password("Admin1234!")
            db.session.add(admin)
            db.session.commit()
            print("✅  Usuario administrador creado.")
            print("    Email:      admin@sgci.com")
            print("    Contraseña: Admin1234!")
        else:
            print("ℹ️   El administrador ya existe, no se creó de nuevo.")


# ---------------------------------------------------------------------------
# Arranque directo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=(flask_env == "development"),
    )
