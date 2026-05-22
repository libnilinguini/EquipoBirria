"""
Modelos de la base de datos – SGCI
Equipo Birria
"""

from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


# ---------------------------------------------------------------------------
# Constantes de dominio
# ---------------------------------------------------------------------------

class RolUsuario:
    ALUMNO        = "alumno"
    PROFESOR      = "profesor"
    ADMINISTRADOR = "administrador"
    TODOS = [ALUMNO, PROFESOR, ADMINISTRADOR]


class EstadoCurso:
    BORRADOR  = "borrador"
    PUBLICADO = "publicado"
    CERRADO   = "cerrado"
    TODOS = [BORRADOR, PUBLICADO, CERRADO]


class TipoMaterial:
    DOCUMENTO = "documento"
    VIDEO     = "video"
    IMAGEN    = "imagen"
    OTRO      = "otro"
    TODOS = [DOCUMENTO, VIDEO, IMAGEN, OTRO]


class EstadoEntrega:
    PENDIENTE  = "pendiente"
    ENTREGADO  = "entregado"
    CALIFICADO = "calificado"
    TODOS = [PENDIENTE, ENTREGADO, CALIFICADO]


# ---------------------------------------------------------------------------
# Tabla asociativa: ayudantes de curso
# ---------------------------------------------------------------------------

ayudantes_curso = db.Table(
    "ayudantes_curso",
    db.Column("curso_id",   db.Integer, db.ForeignKey("curso.id"),   primary_key=True),
    db.Column("usuario_id", db.Integer, db.ForeignKey("usuario.id"), primary_key=True),
)


# ---------------------------------------------------------------------------
# Modelo: Usuario
# ---------------------------------------------------------------------------

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    id             = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(100), nullable=False)
    apellido       = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash  = db.Column(db.String(256), nullable=False)
    rol            = db.Column(db.String(20),  nullable=False, default=RolUsuario.ALUMNO)
    activo         = db.Column(db.Boolean,     nullable=False, default=True)
    fecha_registro = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    # Relaciones
    cursos_impartidos = db.relationship(
        "Curso", backref="profesor", lazy="dynamic",
        foreign_keys="Curso.profesor_id",
    )
    inscripciones = db.relationship(
        "Inscripcion", backref="alumno", lazy="dynamic",
        cascade="all, delete-orphan",
    )
    entregas = db.relationship(
        "Entrega", backref="alumno", lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

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
    __tablename__ = "curso"

    id             = db.Column(db.Integer,    primary_key=True)
    titulo         = db.Column(db.String(150), nullable=False)
    descripcion    = db.Column(db.Text,        nullable=True)
    idioma         = db.Column(db.String(60),  nullable=False)
    nivel          = db.Column(db.String(50),  nullable=False)
    estado         = db.Column(db.String(20),  nullable=False, default=EstadoCurso.BORRADOR)
    fecha_inicio   = db.Column(db.Date,        nullable=True)
    fecha_fin      = db.Column(db.Date,        nullable=True)
    cupo_maximo    = db.Column(db.Integer,     nullable=True)
    fecha_creacion = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    # Contraseña opcional de acceso al curso
    codigo_acceso  = db.Column(db.String(100), nullable=True)

    # Calificaciones habilitadas
    calificaciones_activas = db.Column(db.Boolean, nullable=False, default=False)
    calificacion_minima    = db.Column(db.Float,   nullable=True)   # ej. 6.0
    calificacion_maxima    = db.Column(db.Float,   nullable=True)   # ej. 10.0

    # FK
    profesor_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    # Relaciones
    inscripciones = db.relationship(
        "Inscripcion", backref="curso", lazy="dynamic",
        cascade="all, delete-orphan",
    )
    materiales = db.relationship(
        "Material", backref="curso", lazy="dynamic",
        cascade="all, delete-orphan",
    )
    tareas = db.relationship(
        "Tarea", backref="curso", lazy="dynamic",
        cascade="all, delete-orphan",
    )
    ayudantes = db.relationship(
        "Usuario", secondary=ayudantes_curso, lazy="dynamic",
        backref=db.backref("cursos_ayudados", lazy="dynamic"),
    )

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

    @property
    def inscripcion_abierta(self) -> bool:
        hoy = date.today()
        if self.fecha_inicio and hoy < self.fecha_inicio:
            return False
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        return True

    def es_ayudante(self, usuario) -> bool:
        return self.ayudantes.filter_by(id=usuario.id).first() is not None

    def tiene_acceso(self, usuario) -> bool:
        """Profesor, ayudante o admin tienen acceso completo."""
        return (usuario.es_admin or
                self.profesor_id == usuario.id or
                self.es_ayudante(usuario))

    def publicar(self) -> None:
        self.estado = EstadoCurso.PUBLICADO

    def cerrar(self) -> None:
        self.estado = EstadoCurso.CERRADO

    def __repr__(self) -> str:
        return f"<Curso id={self.id} titulo='{self.titulo}'>"


# ---------------------------------------------------------------------------
# Modelo: Inscripcion
# ---------------------------------------------------------------------------

class Inscripcion(db.Model):
    __tablename__ = "inscripcion"

    id                = db.Column(db.Integer,  primary_key=True)
    fecha_inscripcion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    activa            = db.Column(db.Boolean,  nullable=False, default=True)

    alumno_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    curso_id  = db.Column(db.Integer, db.ForeignKey("curso.id"),   nullable=False)

    __table_args__ = (
        db.UniqueConstraint("alumno_id", "curso_id", name="uq_inscripcion_alumno_curso"),
    )

    def __repr__(self) -> str:
        return f"<Inscripcion alumno_id={self.alumno_id} curso_id={self.curso_id}>"


# ---------------------------------------------------------------------------
# Modelo: Material
# ---------------------------------------------------------------------------

class Material(db.Model):
    __tablename__ = "material"

    id             = db.Column(db.Integer,    primary_key=True)
    titulo         = db.Column(db.String(150), nullable=False)
    descripcion    = db.Column(db.Text,        nullable=True)
    nombre_archivo = db.Column(db.String(260), nullable=False)
    tipo           = db.Column(db.String(20),  nullable=False, default=TipoMaterial.DOCUMENTO)
    fecha_subida   = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    curso_id = db.Column(db.Integer, db.ForeignKey("curso.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<Material id={self.id} titulo='{self.titulo}'>"


# ---------------------------------------------------------------------------
# Modelo: Tarea
# ---------------------------------------------------------------------------

class Tarea(db.Model):
    """
    Actividad entregable definida por el profesor dentro de un curso.
    Los alumnos inscritos pueden subir su Entrega.
    """
    __tablename__ = "tarea"

    id           = db.Column(db.Integer,     primary_key=True)
    titulo       = db.Column(db.String(150),  nullable=False)
    descripcion  = db.Column(db.Text,         nullable=True)
    fecha_limite = db.Column(db.DateTime,     nullable=True)
    fecha_creacion = db.Column(db.DateTime,   nullable=False, default=datetime.utcnow)
    puntaje_max  = db.Column(db.Float,        nullable=True)   # None = sin calificación

    curso_id = db.Column(db.Integer, db.ForeignKey("curso.id"), nullable=False)

    entregas = db.relationship(
        "Entrega", backref="tarea", lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def vencida(self) -> bool:
        return self.fecha_limite is not None and datetime.utcnow() > self.fecha_limite

    def __repr__(self) -> str:
        return f"<Tarea id={self.id} titulo='{self.titulo}'>"


# ---------------------------------------------------------------------------
# Modelo: Entrega
# ---------------------------------------------------------------------------

class Entrega(db.Model):
    """
    Archivo o texto que un alumno sube como respuesta a una Tarea.
    El profesor o ayudante puede calificarla.
    """
    __tablename__ = "entrega"

    id             = db.Column(db.Integer,    primary_key=True)
    nombre_archivo = db.Column(db.String(260), nullable=True)   # puede ser None si solo hay comentario
    comentario     = db.Column(db.Text,        nullable=True)
    calificacion   = db.Column(db.Float,       nullable=True)
    retroalimentacion = db.Column(db.Text,     nullable=True)
    estado         = db.Column(db.String(20),  nullable=False, default=EstadoEntrega.PENDIENTE)
    fecha_entrega  = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    fecha_calificacion = db.Column(db.DateTime, nullable=True)

    alumno_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    tarea_id  = db.Column(db.Integer, db.ForeignKey("tarea.id"),   nullable=False)

    __table_args__ = (
        db.UniqueConstraint("alumno_id", "tarea_id", name="uq_entrega_alumno_tarea"),
    )

    def __repr__(self) -> str:
        return f"<Entrega alumno_id={self.alumno_id} tarea_id={self.tarea_id} estado={self.estado}>"


# ---------------------------------------------------------------------------
# Flask-Login
# ---------------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id: str) -> "Usuario | None":
    return db.session.get(Usuario, int(user_id))
