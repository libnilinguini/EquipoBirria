"""
Controlador de Gestión de Cursos – SGCI
Blueprint: cursos_bp  |  Prefijo: /cursos

Casos de uso cubiertos:
    - Crear curso
    - Editar curso
    - Publicar curso
    - Cerrar curso

Equipo Birria
"""

from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.models import Curso, EstadoCurso

cursos_bp = Blueprint("cursos", __name__, template_folder="../templates/cursos")


# ---------------------------------------------------------------------------
# Decorador: sólo profesores y administradores gestionan cursos
# ---------------------------------------------------------------------------

def profesor_required(f):
    """Restringe el acceso a Profesores y Administradores."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.es_alumno:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def curso_propio_o_admin(curso: Curso) -> bool:
    """Verifica que el usuario sea el dueño del curso o administrador."""
    return current_user.es_admin or curso.profesor_id == current_user.id


# ---------------------------------------------------------------------------
# Listar cursos (ruta de bienvenida post-login)
# ---------------------------------------------------------------------------

@cursos_bp.route("/")
@login_required
def listar_cursos():
    """Muestra los cursos que el usuario puede ver según su rol."""
    if current_user.es_profesor:
        cursos = Curso.query.filter_by(profesor_id=current_user.id).order_by(Curso.fecha_creacion.desc()).all()
    elif current_user.es_admin:
        cursos = Curso.query.order_by(Curso.fecha_creacion.desc()).all()
    else:
        # Alumnos ven sólo cursos publicados
        cursos = Curso.query.filter_by(estado=EstadoCurso.PUBLICADO).order_by(Curso.fecha_creacion.desc()).all()

    return render_template("cursos/listar_cursos.html", cursos=cursos)


# ---------------------------------------------------------------------------
# CU-CUR-01 · Crear curso
# ---------------------------------------------------------------------------

@cursos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@profesor_required
def crear_curso():
    """
    Crea un nuevo curso en estado BORRADOR.

    GET  → Muestra el formulario de creación.
    POST → Valida los datos y persiste el nuevo curso.
    """
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        idioma = request.form.get("idioma", "").strip()
        nivel = request.form.get("nivel", "").strip()
        fecha_inicio_str = request.form.get("fecha_inicio")
        fecha_fin_str = request.form.get("fecha_fin")

        fecha_inicio = (
            datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            if fecha_inicio_str else None
        )

        fecha_fin = (
            datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            if fecha_fin_str else None
        )
        cupo = request.form.get("cupo_maximo")

        if not all([titulo, idioma, nivel]):
            flash("Título, idioma y nivel son obligatorios.", "danger")
            return render_template("cursos/crear_curso.html", form_data=request.form)

        nuevo_curso = Curso(
            titulo=titulo,
            descripcion=descripcion,
            idioma=idioma,
            nivel=nivel,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            cupo_maximo=int(cupo) if cupo else None,
            profesor_id=current_user.id,
        )
        db.session.add(nuevo_curso)
        db.session.commit()
        flash(f"Curso '{titulo}' creado correctamente.", "success")
        return redirect(url_for("cursos.listar_cursos"))

    return render_template("cursos/crear_curso.html", form_data={})


# ---------------------------------------------------------------------------
# CU-CUR-02 · Editar curso
# ---------------------------------------------------------------------------

@cursos_bp.route("/<int:curso_id>/editar", methods=["GET", "POST"])
@login_required
@profesor_required
def editar_curso(curso_id: int):
    """
    Edita los datos de un curso existente.
    Sólo el propietario o un administrador puede editarlo.
    """
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("cursos.listar_cursos"))

    if not curso_propio_o_admin(curso):
        abort(403)

    if curso.estado == EstadoCurso.CERRADO:
        flash("No se puede editar un curso cerrado.", "warning")
        return redirect(url_for("cursos.listar_cursos"))

    if request.method == "POST":
        curso.titulo = request.form.get("titulo", curso.titulo).strip()
        curso.descripcion = request.form.get("descripcion", curso.descripcion).strip()
        curso.idioma = request.form.get("idioma", curso.idioma).strip()
        curso.nivel = request.form.get("nivel", curso.nivel).strip()
        cupo = request.form.get("cupo_maximo")
        curso.cupo_maximo = int(cupo) if cupo else None
        db.session.commit()
        flash("Curso actualizado correctamente.", "success")
        return redirect(url_for("cursos.listar_cursos"))

    return render_template("cursos/editar_curso.html", curso=curso)


# ---------------------------------------------------------------------------
# CU-CUR-03 · Publicar curso
# ---------------------------------------------------------------------------

@cursos_bp.route("/<int:curso_id>/publicar", methods=["POST"])
@login_required
@profesor_required
def publicar_curso(curso_id: int):
    """Cambia el estado del curso de BORRADOR a PUBLICADO."""
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("cursos.listar_cursos"))

    if not curso_propio_o_admin(curso):
        abort(403)

    if curso.estado != EstadoCurso.BORRADOR:
        flash("Solo los cursos en borrador pueden publicarse.", "warning")
        return redirect(url_for("cursos.listar_cursos"))

    curso.publicar()
    db.session.commit()
    flash(f"Curso '{curso.titulo}' publicado exitosamente.", "success")
    return redirect(url_for("cursos.listar_cursos"))


# ---------------------------------------------------------------------------
# CU-CUR-04 · Cerrar curso
# ---------------------------------------------------------------------------

@cursos_bp.route("/<int:curso_id>/cerrar", methods=["POST"])
@login_required
@profesor_required
def cerrar_curso(curso_id: int):
    """Cambia el estado del curso a CERRADO. Esta acción es irreversible."""
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("cursos.listar_cursos"))

    if not curso_propio_o_admin(curso):
        abort(403)

    if curso.estado == EstadoCurso.CERRADO:
        flash("El curso ya está cerrado.", "info")
        return redirect(url_for("cursos.listar_cursos"))

    curso.cerrar()
    db.session.commit()
    flash(f"Curso '{curso.titulo}' cerrado.", "secondary")
    return redirect(url_for("cursos.listar_cursos"))
