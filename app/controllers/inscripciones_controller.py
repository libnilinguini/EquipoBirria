"""
Controlador de Inscripciones – SGCI
Blueprint: inscripciones_bp  |  Prefijo: /inscripciones

Casos de uso cubiertos:
    - CU-INS-01 · Consultar cursos disponibles
    - CU-INS-02 · Inscribirse a un curso

Actor principal: Alumno
Actor secundario: Administrador (puede consultar inscripciones)

Equipo Birria
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.models import Curso, Inscripcion, EstadoCurso, RolUsuario

inscripciones_bp = Blueprint(
    "inscripciones",
    __name__,
    template_folder="../templates/inscripciones",
)


# ---------------------------------------------------------------------------
# CU-INS-01 · Consultar cursos disponibles
# ---------------------------------------------------------------------------

@inscripciones_bp.route("/disponibles")
@login_required
def cursos_disponibles():
    """
    Muestra todos los cursos en estado PUBLICADO a los que el alumno puede inscribirse.

    Flujo normal:
        1. El alumno accede a esta vista.
        2. El sistema consulta los cursos publicados.
        3. El sistema marca cuáles ya tienen al alumno inscrito.
        4. Se muestran los resultados con un botón de inscripción cuando aplica.

    GET → Lista paginada de cursos publicados con filtros por idioma/nivel.
    """
    # Filtros opcionales
    idioma_filtro = request.args.get("idioma", "").strip()
    nivel_filtro = request.args.get("nivel", "").strip()

    query = Curso.query.filter_by(estado=EstadoCurso.PUBLICADO)

    if idioma_filtro:
        query = query.filter(Curso.idioma.ilike(f"%{idioma_filtro}%"))
    if nivel_filtro:
        query = query.filter_by(nivel=nivel_filtro)

    cursos = query.order_by(Curso.fecha_creacion.desc()).all()

    # IDs de cursos en los que el alumno ya está inscrito
    ids_inscritos: set[int] = set()
    if current_user.es_alumno:
        ids_inscritos = {
            insc.curso_id
            for insc in Inscripcion.query.filter_by(
                alumno_id=current_user.id, activa=True
            ).all()
        }

    # Niveles únicos para el filtro del formulario
    niveles = [n[0] for n in db.session.query(Curso.nivel).distinct().all()]

    return render_template(
        "inscripciones/cursos_disponibles.html",
        cursos=cursos,
        ids_inscritos=ids_inscritos,
        idioma_filtro=idioma_filtro,
        nivel_filtro=nivel_filtro,
        niveles=niveles,
    )


# ---------------------------------------------------------------------------
# CU-INS-02 · Inscribirse a un curso
# ---------------------------------------------------------------------------

@inscripciones_bp.route("/<int:curso_id>/inscribirse", methods=["POST"])
@login_required
def inscribirse(curso_id: int):
    """
    Registra formalmente al alumno en el curso seleccionado.

    Precondiciones:
        - El usuario debe tener rol Alumno.
        - El curso debe estar en estado PUBLICADO.
        - El alumno no debe estar ya inscrito.
        - El curso debe tener cupo disponible (si aplica).

    Flujo normal:
        1. El alumno hace clic en "Inscribirse" en la vista de cursos disponibles.
        2. El sistema verifica precondiciones.
        3. Se crea el registro de Inscripcion.
        4. El sistema muestra confirmación y redirige.

    POST → Crea la inscripción y redirige a la lista de cursos disponibles.
    """
    if not current_user.es_alumno:
        flash("Solo los alumnos pueden inscribirse a cursos.", "warning")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("El curso solicitado no existe.", "danger")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    # Verificar estado
    if not curso.es_publicado:
        flash("No es posible inscribirse a un curso que no está publicado.", "warning")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    # Verificar cupo
    if not curso.tiene_cupo:
        flash(f"El curso '{curso.titulo}' ya no tiene cupo disponible.", "warning")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    # Verificar inscripción previa
    existente = Inscripcion.query.filter_by(
        alumno_id=current_user.id, curso_id=curso_id
    ).first()
    if existente:
        flash("Ya estás inscrito en este curso.", "info")
        return redirect(url_for("inscripciones.mis_inscripciones"))

    try:
        nueva_inscripcion = Inscripcion(
            alumno_id=current_user.id,
            curso_id=curso_id,
        )
        db.session.add(nueva_inscripcion)
        db.session.commit()
        flash(f"¡Inscripción exitosa al curso '{curso.titulo}'!", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Ya existe una inscripción para este curso.", "info")

    return redirect(url_for("inscripciones.mis_inscripciones"))


# ---------------------------------------------------------------------------
# Ruta auxiliar · Mis inscripciones
# ---------------------------------------------------------------------------

@inscripciones_bp.route("/mis-inscripciones")
@login_required
def mis_inscripciones():
    """
    Lista los cursos en los que el alumno actual está inscrito.

    GET → Vista personal de inscripciones activas.
    """
    if not current_user.es_alumno:
        flash("Esta sección es exclusiva para alumnos.", "warning")
        return redirect(url_for("cursos.listar_cursos"))

    inscripciones = (
        Inscripcion.query
        .filter_by(alumno_id=current_user.id, activa=True)
        .order_by(Inscripcion.fecha_inscripcion.desc())
        .all()
    )
    return render_template(
        "inscripciones/mis_inscripciones.html",
        inscripciones=inscripciones,
    )


# ---------------------------------------------------------------------------
# Ruta auxiliar · Cancelar inscripción
# ---------------------------------------------------------------------------

@inscripciones_bp.route("/<int:inscripcion_id>/cancelar", methods=["POST"])
@login_required
def cancelar_inscripcion(inscripcion_id: int):
    """
    Desactiva una inscripción existente del alumno actual.

    POST → Marca la inscripción como inactiva y redirige.
    """
    inscripcion = db.session.get(Inscripcion, inscripcion_id)
    if not inscripcion or inscripcion.alumno_id != current_user.id:
        flash("Inscripción no encontrada.", "danger")
        return redirect(url_for("inscripciones.mis_inscripciones"))

    inscripcion.activa = False
    db.session.commit()
    flash("Inscripción cancelada.", "secondary")
    return redirect(url_for("inscripciones.mis_inscripciones"))
