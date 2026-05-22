"""
Controlador de Tareas y Entregas – SGCI
Blueprint: tareas_bp  |  Prefijo: /tareas
Equipo Birria
"""

import os
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort, current_app)
from flask_login import login_required, current_user

from app import db
from app.models.models import (Curso, Tarea, Entrega, Inscripcion,
                                EstadoEntrega, EstadoCurso)

tareas_bp = Blueprint("tareas", __name__, template_folder="../templates/tareas")


def _tiene_acceso_curso(curso):
    """Profesor dueño, ayudante o admin."""
    return curso.tiene_acceso(current_user)


def _alumno_inscrito(curso):
    return Inscripcion.query.filter_by(
        alumno_id=current_user.id, curso_id=curso.id, activa=True
    ).first() is not None


# ─────────────────────────────────────────────
# TAREAS: CRUD (profesor/ayudante)
# ─────────────────────────────────────────────

@tareas_bp.route("/<int:curso_id>/")
@login_required
def listar_tareas(curso_id):
    curso = db.session.get(Curso, curso_id)
    if not curso:
        abort(404)

    es_staff = _tiene_acceso_curso(curso)
    es_alumno_inscrito = current_user.es_alumno and _alumno_inscrito(curso)

    if not es_staff and not es_alumno_inscrito:
        abort(403)

    tareas = curso.tareas.order_by(Tarea.fecha_creacion.desc()).all()

    # Para alumnos: qué tareas ya entregaron
    mis_entregas = {}
    if current_user.es_alumno:
        for e in Entrega.query.filter_by(alumno_id=current_user.id).all():
            mis_entregas[e.tarea_id] = e

    return render_template("tareas/listar_tareas.html",
                           curso=curso,
                           tareas=tareas,
                           es_staff=es_staff,
                           mis_entregas=mis_entregas)


@tareas_bp.route("/<int:curso_id>/crear", methods=["GET", "POST"])
@login_required
def crear_tarea(curso_id):
    curso = db.session.get(Curso, curso_id)
    if not curso or not _tiene_acceso_curso(curso):
        abort(403)

    if request.method == "POST":
        titulo      = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        fecha_lim   = request.form.get("fecha_limite", "").strip()
        puntaje     = request.form.get("puntaje_max", "").strip()

        if not titulo:
            flash("El título es obligatorio.", "danger")
            return render_template("tareas/crear_tarea.html", curso=curso)

        fecha_limite = None
        if fecha_lim:
            try:
                fecha_limite = datetime.strptime(fecha_lim, "%Y-%m-%dT%H:%M")
            except ValueError:
                pass

        tarea = Tarea(
            titulo=titulo,
            descripcion=descripcion,
            fecha_limite=fecha_limite,
            puntaje_max=float(puntaje) if puntaje else None,
            curso_id=curso_id,
        )
        db.session.add(tarea)
        db.session.commit()
        flash(f"Tarea '{titulo}' creada.", "success")
        return redirect(url_for("tareas.listar_tareas", curso_id=curso_id))

    return render_template("tareas/crear_tarea.html", curso=curso)


@tareas_bp.route("/<int:curso_id>/eliminar/<int:tarea_id>", methods=["POST"])
@login_required
def eliminar_tarea(curso_id, tarea_id):
    curso = db.session.get(Curso, curso_id)
    if not curso or not _tiene_acceso_curso(curso):
        abort(403)
    tarea = db.session.get(Tarea, tarea_id)
    if not tarea or tarea.curso_id != curso_id:
        abort(404)
    db.session.delete(tarea)
    db.session.commit()
    flash("Tarea eliminada.", "secondary")
    return redirect(url_for("tareas.listar_tareas", curso_id=curso_id))


# ─────────────────────────────────────────────
# ENTREGAS: alumno sube, profesor califica
# ─────────────────────────────────────────────

@tareas_bp.route("/<int:curso_id>/tarea/<int:tarea_id>/entregar", methods=["GET", "POST"])
@login_required
def entregar(curso_id, tarea_id):
    curso = db.session.get(Curso, curso_id)
    if not curso:
        abort(404)
    if not current_user.es_alumno or not _alumno_inscrito(curso):
        abort(403)

    tarea = db.session.get(Tarea, tarea_id)
    if not tarea or tarea.curso_id != curso_id:
        abort(404)

    entrega_existente = Entrega.query.filter_by(
        alumno_id=current_user.id, tarea_id=tarea_id
    ).first()

    if request.method == "POST":
        comentario = request.form.get("comentario", "").strip()
        archivo    = request.files.get("archivo")
        nombre_guardado = None

        if archivo and archivo.filename:
            ext = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
            if ext in current_app.config.get("ALLOWED_EXTENSIONS", set()):
                nombre_seguro   = secure_filename(archivo.filename)
                nombre_guardado = f"entrega_t{tarea_id}_u{current_user.id}_{nombre_seguro}"
                ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_guardado)
                archivo.save(ruta)
            else:
                flash("Tipo de archivo no permitido.", "danger")
                return render_template("tareas/entregar.html",
                                       curso=curso, tarea=tarea, entrega=entrega_existente)

        if not comentario and not nombre_guardado:
            flash("Debes escribir un comentario o adjuntar un archivo.", "danger")
            return render_template("tareas/entregar.html",
                                   curso=curso, tarea=tarea, entrega=entrega_existente)

        if entrega_existente:
            entrega_existente.comentario     = comentario
            entrega_existente.estado         = EstadoEntrega.ENTREGADO
            entrega_existente.fecha_entrega  = datetime.utcnow()
            if nombre_guardado:
                entrega_existente.nombre_archivo = nombre_guardado
            db.session.commit()
            flash("Entrega actualizada.", "success")
        else:
            nueva = Entrega(
                alumno_id=current_user.id,
                tarea_id=tarea_id,
                comentario=comentario,
                nombre_archivo=nombre_guardado,
                estado=EstadoEntrega.ENTREGADO,
            )
            db.session.add(nueva)
            db.session.commit()
            flash("¡Entrega realizada con éxito!", "success")

        return redirect(url_for("tareas.listar_tareas", curso_id=curso_id))

    return render_template("tareas/entregar.html",
                           curso=curso, tarea=tarea, entrega=entrega_existente)


@tareas_bp.route("/<int:curso_id>/tarea/<int:tarea_id>/entregas")
@login_required
def ver_entregas(curso_id, tarea_id):
    curso = db.session.get(Curso, curso_id)
    if not curso or not _tiene_acceso_curso(curso):
        abort(403)
    tarea = db.session.get(Tarea, tarea_id)
    if not tarea or tarea.curso_id != curso_id:
        abort(404)

    entregas = Entrega.query.filter_by(tarea_id=tarea_id).all()
    return render_template("tareas/ver_entregas.html",
                           curso=curso, tarea=tarea, entregas=entregas)


@tareas_bp.route("/<int:curso_id>/tarea/<int:tarea_id>/calificar/<int:entrega_id>",
                 methods=["GET", "POST"])
@login_required
def calificar(curso_id, tarea_id, entrega_id):
    curso = db.session.get(Curso, curso_id)
    if not curso or not _tiene_acceso_curso(curso):
        abort(403)

    tarea   = db.session.get(Tarea, tarea_id)
    entrega = db.session.get(Entrega, entrega_id)
    if not tarea or not entrega or entrega.tarea_id != tarea_id:
        abort(404)

    if request.method == "POST":
        cal_str = request.form.get("calificacion", "").strip()
        retro   = request.form.get("retroalimentacion", "").strip()

        if cal_str:
            try:
                cal = float(cal_str)
                # validar rango si el curso lo tiene configurado
                if curso.calificaciones_activas:
                    mn = curso.calificacion_minima
                    mx = curso.calificacion_maxima
                    if mn is not None and cal < mn:
                        flash(f"La calificación no puede ser menor a {mn}.", "danger")
                        return render_template("tareas/calificar.html",
                                               curso=curso, tarea=tarea, entrega=entrega)
                    if mx is not None and cal > mx:
                        flash(f"La calificación no puede ser mayor a {mx}.", "danger")
                        return render_template("tareas/calificar.html",
                                               curso=curso, tarea=tarea, entrega=entrega)
                entrega.calificacion        = cal
                entrega.estado              = EstadoEntrega.CALIFICADO
                entrega.fecha_calificacion  = datetime.utcnow()
            except ValueError:
                flash("Calificación inválida.", "danger")
                return render_template("tareas/calificar.html",
                                       curso=curso, tarea=tarea, entrega=entrega)

        entrega.retroalimentacion = retro
        db.session.commit()
        flash("Entrega calificada correctamente.", "success")
        return redirect(url_for("tareas.ver_entregas",
                                curso_id=curso_id, tarea_id=tarea_id))

    return render_template("tareas/calificar.html",
                           curso=curso, tarea=tarea, entrega=entrega)
