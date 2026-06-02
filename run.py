"""
run.py – Punto de Entrada Principal del SGCI (Sistema de Gestión de Cursos de Idiomas)

Equipo de Desarrollo: Birria
Año: 2026

Este script actúa como el orquestador global de la aplicación. Se encarga de
inicializar el servidor web, configurar el contexto de ejecución interactivo, 
gestionar los comandos de consola personalizados (CLI) y arrancar la aplicación
en el entorno correspondiente.

Uso en Terminal:
    python run.py                   # Inicia en modo desarrollo (por defecto)
    FLASK_ENV=production python run.py # Inicia en modo producción

Variables de Entorno Clave:
    FLASK_ENV    → Define el entorno ('development', 'testing', 'production'). Default: development.
    SECRET_KEY   → Llave criptográfica de la app (Mandatoria en producción).
    DATABASE_URL → URI de conexión para SQLAlchemy (Default: SQLite local).
    PORT         → Puerto de escucha del servidor web (Default: 5000).
"""

import os
from app import create_app, db
from app.models.models import Usuario, Curso, Inscripcion, Material, RolUsuario, Tarea, Entrega

# 1. Detección de Entorno y Creación de la Aplicación
# Se lee la variable del sistema; si no existe, se asume un enfoque seguro para desarrollo.
flask_env = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name=flask_env)


# ---------------------------------------------------------------------------
# Shell Context: Entorno de Depuración Interactiva
# ---------------------------------------------------------------------------

@app.shell_context_processor
def make_shell_context():
    """
    Inyecta automáticamente los modelos del sistema y la base de datos en el REPL.
    
    Permite a los desarrolladores realizar consultas, pruebas rápidas de lógica y
    manipulación de datos directamente desde la terminal sin necesidad de importar
    manualmente cada clase en cada sesión.
    
    Ejecutar con:
        flask shell
        
    Returns:
        dict: Mapeo de variables que estarán disponibles en el espacio de nombres del shell.
    """
    return {
        "db": db,
        "Usuario": Usuario,
        "Curso": Curso,
        "Inscripcion": Inscripcion,
        "Material": Material,
        "Tarea": Tarea,
        "Entrega": Entrega,
    }


# ---------------------------------------------------------------------------
# Comando CLI: Inicialización y Aprovisionamiento del Sistema
# ---------------------------------------------------------------------------

@app.cli.command("init-db")
def init_db():
    """
    Inicializa el almacenamiento y crea una cuenta raíz de administración.
    
    Este comando realiza dos acciones críticas de infraestructura:
    1. Ejecuta db.create_all() para mapear y estructurar las tablas en la BD actual.
    2. Valida la existencia del Administrador por defecto; si está ausente, 
       lo siembra (seed) con credenciales iniciales para el primer inicio de sesión.

    Ejecutar con:
        flask init-db
    """
    with app.app_context():
        # Creación del esquema físico de la Base de Datos
        db.create_all()
        print("✅  Tablas creadas correctamente.")

        # Flujo de Control: Verificación de Usuario Administrador Primario
        if not Usuario.query.filter_by(email="admin@sgci.com").first():
            admin = Usuario(
                nombre="Admin",
                apellido="SGCI",
                email="admin@sgci.com",
                rol=RolUsuario.ADMINISTRADOR,
            )
            # Aplicación de hashing seguro para la credencial de acceso
            admin.set_password("Admin1234!")
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅  Usuario administrador creado con éxito.")
            print("    Email:      admin@sgci.com")
            print("    Contraseña: Admin1234!")
        else:
            print("ℹ️   El administrador ya existe en el sistema. Omitiendo inicialización.")


# ---------------------------------------------------------------------------
# Arranque Directo del Servidor Web
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Punto de arranque nativo de Python.
    
    Configura los parámetros perimetrales del servidor HTTP integrado de Flask:
    - host: '0.0.0.0' expone el servidor localmente y en la red de área local.
    - port: Enlaza dinámicamente con el puerto asignado por el entorno (útil para Cloud Services).
    - debug: Activa el reajuste en caliente (Hot Reloading) y el depurador visual solo en Desarrollo.
    """
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=(flask_env == "development"),
    )