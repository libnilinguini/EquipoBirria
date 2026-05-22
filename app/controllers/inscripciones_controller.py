"""
Controlador de Inscripciones – SGCI
Blueprint: inscripciones_bp  |  Prefijo: /inscripciones

Casos de uso cubiertos:
    - CU-INS-01 · Consultar cursos disponibles
    - CU-INS-02 · Inscribirse a un curso

Actor principal: Alumno
Equipo Birria
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.models import Curso, Inscripcion, EstadoCurso

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
    """Lista cursos PUBLICADOS con filtros opcionales."""

    idioma_filtro = request.args.get("idioma", "").strip()
    nivel_filtro  = request.args.get("nivel",  "").strip()

    query = Curso.query.filter_by(estado=EstadoCurso.PUBLICADO)

    if idioma_filtro:
        query = query.filter(Curso.idioma.ilike(f"%{idioma_filtro}%"))
    if nivel_filtro:
        query = query.filter_by(nivel=nivel_filtro)

    cursos = query.order_by(Curso.fecha_creacion.desc()).all()

    # IDs en los que el alumno ya está inscrito (activos)
    ids_inscritos: set[int] = set()
    if current_user.es_alumno:
        ids_inscritos = {
            i.curso_id
            for i in Inscripcion.query.filter_by(
                alumno_id=current_user.id, activa=True
            ).all()
        }

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
    Registra al alumno en el curso indicado.

    Validaciones (en orden):
        1. El usuario debe ser Alumno.
        2. El curso debe existir.
        3. El curso debe estar PUBLICADO.
        4. Las fechas de inscripción deben ser válidas (BUG FIX).
        5. El curso debe tener cupo disponible.
        6. El alumno no debe estar ya inscrito.
    """

    # 1 · Solo alumnos
    if not current_user.es_alumno:
        flash("Solo los alumnos pueden inscribirse a cursos.", "warning")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    # 2 · Curso debe existir
    try:
        curso = db.session.get(Curso, curso_id)
    except Exception:
        flash("Ocurrió un error al buscar el curso. Intenta de nuevo.", "danger")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    if not curso:
        flash("El curso solicitado no existe.", "danger")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    # 3 · Curso debe estar publicado
    if not curso.es_publicado:
        flash("No es posible inscribirse a un curso que no está publicado.", "warning")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    # 4 · Validar fechas de inscripción  ← BUG FIX PRINCIPAL
    if not curso.inscripcion_abierta:
        from datetime import date
        hoy = date.today()

        if curso.fecha_fin and hoy > curso.fecha_fin:
            flash(
                f"El período de inscripción para '{curso.titulo}' cerró el "
                f"{curso.fecha_fin.strftime('%d/%m/%Y')}. Ya no es posible inscribirse.",
                "warning",
            )
        elif curso.fecha_inicio and hoy < curso.fecha_inicio:
            flash(
                f"Las inscripciones para '{curso.titulo}' abren el "
                f"{curso.fecha_inicio.strftime('%d/%m/%Y')}.",
                "info",
            )
        else:
            flash("Las inscripciones para este curso no están disponibles en este momento.", "warning")

        return redirect(url_for("inscripciones.cursos_disponibles"))

    # 5 · Verificar cupo
    if not curso.tiene_cupo:
        flash(f"El curso '{curso.titulo}' ya no tiene cupo disponible.", "warning")
        return redirect(url_for("inscripciones.cursos_disponibles"))

    # 6 · Verificar inscripción previa
    existente = Inscripcion.query.filter_by(
        alumno_id=current_user.id, curso_id=curso_id
    ).first()
    if existente:
        if existente.activa:
            flash("Ya estás inscrito en este curso.", "info")
        else:
            # Reactivar inscripción cancelada anteriormente
            existente.activa = True
            db.session.commit()
            flash(f"Tu inscripción a '{curso.titulo}' ha sido reactivada.", "success")
        return redirect(url_for("inscripciones.mis_inscripciones"))

    # Todo OK → crear inscripción
    try:
        nueva = Inscripcion(
            alumno_id=current_user.id,
            curso_id=curso_id,
        )
        db.session.add(nueva)
        db.session.commit()
        flash(f"¡Inscripción exitosa al curso '{curso.titulo}'!", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Ya existe una inscripción registrada para este curso.", "info")
    except Exception:
        db.session.rollback()
        flash("Ocurrió un error al procesar tu inscripción. Intenta de nuevo.", "danger")

    return redirect(url_for("inscripciones.mis_inscripciones"))


# ---------------------------------------------------------------------------
# Ruta auxiliar · Mis inscripciones
# ---------------------------------------------------------------------------

@inscripciones_bp.route("/mis-inscripciones")
@login_required
def mis_inscripciones():
    """Lista las inscripciones activas del alumno actual."""

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
    """Desactiva una inscripción activa del alumno actual."""

    try:
        inscripcion = db.session.get(Inscripcion, inscripcion_id)
    except Exception:
        flash("Error al buscar la inscripción.", "danger")
        return redirect(url_for("inscripciones.mis_inscripciones"))

    if not inscripcion or inscripcion.alumno_id != current_user.id:
        flash("Inscripción no encontrada.", "danger")
        return redirect(url_for("inscripciones.mis_inscripciones"))

    if not inscripcion.activa:
        flash("Esta inscripción ya estaba cancelada.", "info")
        return redirect(url_for("inscripciones.mis_inscripciones"))

    try:
        inscripcion.activa = False
        db.session.commit()
        flash(f"Inscripción al curso '{inscripcion.curso.titulo}' cancelada.", "secondary")
    except Exception:
        db.session.rollback()
        flash("Error al cancelar la inscripción. Intenta de nuevo.", "danger")

    return redirect(url_for("inscripciones.mis_inscripciones"))
