# SGCI — Sistema de Gestión de Cursos de Idiomas
**Equipo Birria** · Proyecto de Software

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3 · Flask 3 |
| ORM | SQLAlchemy 2 + Flask-SQLAlchemy |
| Autenticación | Flask-Login |
| Frontend | Jinja2 + Bootstrap 5 |
| BD (dev) | SQLite |
| BD (prod) | PostgreSQL 16 |
| Control de versiones | Git / GitHub |

---

## Estructura del proyecto

```
sgci/
├── run.py                        # Punto de entrada
├── config.py                     # Configuración por entorno
├── requirements.txt
├── app/
│   ├── __init__.py               # Application factory
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py             # Usuario · Curso · Inscripcion · Material
│   ├── controllers/              # Blueprints (MVC – Controladores)
│   │   ├── auth_controller.py         # Autenticación
│   │   ├── admin_controller.py        # Administración
│   │   ├── cursos_controller.py       # Gestión de Cursos
│   │   ├── materiales_controller.py   # Materiales
│   │   └── inscripciones_controller.py# Inscripciones
│   ├── templates/                # Jinja2 (MVC – Vistas)
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── admin/
│   │   ├── cursos/
│   │   ├── materiales/
│   │   └── inscripciones/
│   └── static/
│       ├── css/
│       ├── js/
│       ├── img/
│       └── uploads/              # Archivos de materiales (gitignore)
└── tests/                        # test_*.py del equipo
```

---

## Instalación y arranque

```bash
# 1. Clonar el repo
git clone https://github.com/gomugomu999/Equipo-Birria-3.git
cd Equipo-Birria-3

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar la base de datos (crea tablas + admin de ejemplo)
flask init-db

# 5. Ejecutar el servidor de desarrollo
python run.py
```

La app estará disponible en **http://localhost:5000**

**Credenciales del administrador inicial:**
- Email: `admin@sgci.com`
- Contraseña: `Admin1234!`

---

## Módulos y casos de uso (16 CU)

| # | Módulo | Caso de Uso | Ruta |
|---|--------|------------|------|
| 1 | Autenticación | Registrarse | `GET/POST /auth/registro` |
| 2 | Autenticación | Iniciar sesión | `GET/POST /auth/login` |
| 3 | Autenticación | Cerrar sesión | `GET /auth/logout` |
| 4 | Administración | Gestionar usuarios | `GET /admin/usuarios` |
| 5 | Administración | Asignar roles | `GET/POST /admin/usuarios/<id>/rol` |
| 6 | Administración | Cambiar estado del curso | `POST /admin/cursos/<id>/estado` |
| 7 | Administración | Consultar cursos | `GET /admin/cursos` |
| 8 | Gestión de Cursos | Crear curso | `GET/POST /cursos/crear` |
| 9 | Gestión de Cursos | Editar curso | `GET/POST /cursos/<id>/editar` |
| 10 | Gestión de Cursos | Publicar curso | `POST /cursos/<id>/publicar` |
| 11 | Gestión de Cursos | Cerrar curso | `POST /cursos/<id>/cerrar` |
| 12 | Materiales | Subir material | `GET/POST /materiales/<curso_id>/subir` |
| 13 | Materiales | Gestionar materiales | `GET /materiales/<curso_id>/gestionar` |
| 14 | Materiales | Consultar materiales | `GET /materiales/<curso_id>/consultar` |
| 15 | Inscripciones | Consultar cursos disponibles | `GET /inscripciones/disponibles` |
| 16 | Inscripciones | Inscribirse a curso | `POST /inscripciones/<curso_id>/inscribirse` |

---

## Pruebas unitarias

```bash
# Ejecutar todos los tests del equipo
python -m pytest tests/ -v
```

Los tests deben usar `config_name="testing"` al llamar `create_app()`.

---

## Equipo Birria
- Hernández Torres Marco Antonio — Líder del Equipo
- Morales Silva Libni Jael — Líder Técnico
- Gomez Calva Carlos Manuel — Líder de Colaboración
- González Cerón Romario — Líder de Colaboración
- Pimentel Sánchez Alexia Michelle — Líder de Calidad

Docente: Francisco Valdés Souto
