"""
Modelos de la base de datos – SGCI
Basados en el Diagrama Entidad-Relación del documento de Diseño de Software.

Tablas:  Usuario · Curso · Inscripcion · Material
Equipo Birria
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

# ---------------------------------------------------------------------------
# Constantes de dominio
# ---------------------------------------------------------------------------

class RolUsuario:
    ALUMNO = "alumno"
    PROFESOR = "profesor"
    ADMINISTRADOR = "administrador"
    TODOS = [ALUMNO, PROFESOR, ADMINISTRADOR]


class EstadoCurso:
    BORRADOR = "borrador"
    PUBLICADO = "publicado"
    CERRADO = "cerrado"
    TODOS = [BORRADOR, PUBLICADO, CERRADO]


class TipoMaterial:
    DOCUMENTO = "documento"
    VIDEO = "video"
    IMAGEN = "imagen"
    OTRO = "otro"
    TODOS = [DOCUMENTO, VIDEO, IMAGEN, OTRO]


# ---------------------------------------------------------------------------
# Modelo: Usuario
# ---------------------------------------------------------------------------

class Usuario(UserMixin, db.Model):
    """
    Representa a cualquier persona registrada en el SGCI.
    Puede ser Alumno, Profesor o Administrador según el campo ``rol``.

    Relaciones:
        - cursos_impartidos  →  Curso  (uno a muchos, como profesor)
        - inscripciones      →  Inscripcion  (uno a muchos)
    """

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=RolUsuario.ALUMNO)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relaciones
    cursos_impartidos = db.relationship(
        "Curso",
        backref="profesor",
        lazy="dynamic",
        foreign_keys="Curso.profesor_id",
    )
    inscripciones = db.relationship(
        "Inscripcion",
        backref="alumno",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # Helpers de contraseña
    # ------------------------------------------------------------------

    def set_password(self, password: str) -> None:
        """Genera y almacena el hash de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica si la contraseña en texto plano coincide con el hash."""
        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------
    # Helpers de rol
    # ------------------------------------------------------------------

    @property
    def es_admin(self) -> bool:
        return self.rol == RolUsuario.ADMINISTRADOR

    @property
    def es_profesor(self) -> bool:
        return self.rol == RolUsuario.PROFESOR

    @property
    def es_alumno(self) -> bool:
        return self.rol == RolUsuario.ALUMNO

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email} rol={self.rol}>"


# ---------------------------------------------------------------------------
# Modelo: Curso
# ---------------------------------------------------------------------------

class Curso(db.Model):
    """
    Unidad académica ofrecida por un Profesor.
    Contiene idioma, nivel, fechas y descripción definidos.

    Relaciones:
        - profesor       →  Usuario  (muchos a uno)
        - inscripciones  →  Inscripcion  (uno a muchos)
        - materiales     →  Material  (uno a muchos)
    """

    __tablename__ = "curso"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    idioma = db.Column(db.String(60), nullable=False)
    nivel = db.Column(db.String(50), nullable=False)   # Ej: A1, A2, B1, B2, C1, C2
    estado = db.Column(db.String(20), nullable=False, default=EstadoCurso.BORRADOR)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    cupo_maximo = db.Column(db.Integer, nullable=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # FK
    profesor_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    # Relaciones
    inscripciones = db.relationship(
        "Inscripcion",
        backref="curso",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    materiales = db.relationship(
        "Material",
        backref="curso",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # Helpers de estado
    # ------------------------------------------------------------------

    @property
    def es_publicado(self) -> bool:
        return self.estado == EstadoCurso.PUBLICADO

    @property
    def total_inscritos(self) -> int:
        return self.inscripciones.count()

    @property
    def tiene_cupo(self) -> bool:
        if self.cupo_maximo is None:
            return True
        return self.total_inscritos < self.cupo_maximo

    def publicar(self) -> None:
        """Cambia el estado del curso a PUBLICADO."""
        self.estado = EstadoCurso.PUBLICADO

    def cerrar(self) -> None:
        """Cambia el estado del curso a CERRADO."""
        self.estado = EstadoCurso.CERRADO

    def __repr__(self) -> str:
        return f"<Curso id={self.id} titulo='{self.titulo}' estado={self.estado}>"


# ---------------------------------------------------------------------------
# Modelo: Inscripcion
# ---------------------------------------------------------------------------

class Inscripcion(db.Model):
    """
    Registro formal de un Alumno en un Curso publicado.

    Relaciones:
        - alumno  →  Usuario  (muchos a uno)
        - curso   →  Curso    (muchos a uno)
    """

    __tablename__ = "inscripcion"

    id = db.Column(db.Integer, primary_key=True)
    fecha_inscripcion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    activa = db.Column(db.Boolean, nullable=False, default=True)

    # FK
    alumno_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey("curso.id"), nullable=False)

    # Restricción de unicidad: un alumno no puede inscribirse dos veces al mismo curso
    __table_args__ = (
        db.UniqueConstraint("alumno_id", "curso_id", name="uq_inscripcion_alumno_curso"),
    )

    def __repr__(self) -> str:
        return f"<Inscripcion alumno_id={self.alumno_id} curso_id={self.curso_id}>"


# ---------------------------------------------------------------------------
# Modelo: Material
# ---------------------------------------------------------------------------

class Material(db.Model):
    """
    Archivo educativo (documento, video, imagen) asociado a un Curso.
    Accesible para los alumnos inscritos.

    Relaciones:
        - curso  →  Curso  (muchos a uno)
    """

    __tablename__ = "material"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    nombre_archivo = db.Column(db.String(260), nullable=False)   # nombre en disco
    tipo = db.Column(db.String(20), nullable=False, default=TipoMaterial.DOCUMENTO)
    fecha_subida = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # FK
    curso_id = db.Column(db.Integer, db.ForeignKey("curso.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<Material id={self.id} titulo='{self.titulo}' curso_id={self.curso_id}>"


# ---------------------------------------------------------------------------
# Callback requerido por Flask-Login
# ---------------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id: str) -> "Usuario | None":
    """Carga el usuario desde la base de datos usando su ID de sesión."""
    return db.session.get(Usuario, int(user_id))
