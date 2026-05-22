"""
Controlador de Gestión de Cursos – SGCI
Blueprint: cursos_bp  |  Prefijo: /cursos
Equipo Birria
"""

from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.models import Curso, EstadoCurso, Usuario, RolUsuario, ayudantes_curso

cursos_bp = Blueprint("cursos", __name__, template_folder="../templates/cursos")


def _parse_date(valor: str):
    if not valor or not valor.strip():
        return None
    try:
        return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def profesor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.es_alumno:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def curso_propio_o_admin(curso: Curso) -> bool:
    return current_user.es_admin or curso.profesor_id == current_user.id


# ---------------------------------------------------------------------------
# Listar cursos
# ---------------------------------------------------------------------------

@cursos_bp.route("/")
@login_required
def listar_cursos():
    if current_user.es_profesor:
        # cursos propios + cursos donde es ayudante
        propios   = Curso.query.filter_by(profesor_id=current_user.id)
        ayudados  = current_user.cursos_ayudados
        cursos    = propios.union(ayudados).order_by(Curso.fecha_creacion.desc()).all()
    elif current_user.es_admin:
        cursos = Curso.query.order_by(Curso.fecha_creacion.desc()).all()
    else:
        cursos = Curso.query.filter_by(estado=EstadoCurso.PUBLICADO).order_by(Curso.fecha_creacion.desc()).all()

    return render_template("cursos/listar_cursos.html", cursos=cursos)


# ---------------------------------------------------------------------------
# Crear curso
# ---------------------------------------------------------------------------

@cursos_bp.route("/crear", methods=["GET", "POST"])
@login_required
@profesor_required
def crear_curso():
    profesores = Usuario.query.filter_by(rol=RolUsuario.PROFESOR, activo=True).all()

    if request.method == "POST":
        titulo       = request.form.get("titulo", "").strip()
        descripcion  = request.form.get("descripcion", "").strip()
        idioma       = request.form.get("idioma", "").strip()
        nivel        = request.form.get("nivel", "").strip()
        cupo         = request.form.get("cupo_maximo", "").strip()
        codigo       = request.form.get("codigo_acceso", "").strip() or None
        fecha_inicio = _parse_date(request.form.get("fecha_inicio", ""))
        fecha_fin    = _parse_date(request.form.get("fecha_fin", ""))

        # Calificaciones
        cal_activas  = request.form.get("calificaciones_activas") == "on"
        cal_min      = request.form.get("calificacion_minima", "").strip()
        cal_max      = request.form.get("calificacion_maxima", "").strip()

        # Ayudantes seleccionados
        ayudante_ids = request.form.getlist("ayudantes")

        if not all([titulo, idioma, nivel]):
            flash("Título, idioma y nivel son obligatorios.", "danger")
            return render_template("cursos/crear_curso.html", form_data=request.form, profesores=profesores)

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "danger")
            return render_template("cursos/crear_curso.html", form_data=request.form, profesores=profesores)

        try:
            nuevo_curso = Curso(
                titulo=titulo,
                descripcion=descripcion,
                idioma=idioma,
                nivel=nivel,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                cupo_maximo=int(cupo) if cupo else None,
                profesor_id=current_user.id,
                codigo_acceso=codigo,
                calificaciones_activas=cal_activas,
                calificacion_minima=float(cal_min) if cal_min else None,
                calificacion_maxima=float(cal_max) if cal_max else None,
            )
            db.session.add(nuevo_curso)
            db.session.flush()  # genera ID antes de agregar ayudantes

            for aid in ayudante_ids:
                ayudante = db.session.get(Usuario, int(aid))
                if ayudante and ayudante.es_profesor and ayudante.id != current_user.id:
                    nuevo_curso.ayudantes.append(ayudante)

            db.session.commit()
            flash(f"Curso '{titulo}' creado correctamente.", "success")
            return redirect(url_for("cursos.listar_cursos"))
        except Exception as e:
            db.session.rollback()
            flash("Error al crear el curso. Verifica los datos.", "danger")

    return render_template("cursos/crear_curso.html",
                           form_data={},
                           profesores=profesores)


# ---------------------------------------------------------------------------
# Editar curso
# ---------------------------------------------------------------------------

@cursos_bp.route("/<int:curso_id>/editar", methods=["GET", "POST"])
@login_required
@profesor_required
def editar_curso(curso_id: int):
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("cursos.listar_cursos"))

    if not curso_propio_o_admin(curso):
        abort(403)

    if curso.estado == EstadoCurso.CERRADO:
        flash("No se puede editar un curso cerrado.", "warning")
        return redirect(url_for("cursos.listar_cursos"))

    profesores = Usuario.query.filter_by(rol=RolUsuario.PROFESOR, activo=True).all()
    ayudantes_actuales = [u.id for u in curso.ayudantes.all()]

    if request.method == "POST":
        titulo       = request.form.get("titulo", "").strip()
        descripcion  = request.form.get("descripcion", "").strip()
        idioma       = request.form.get("idioma", "").strip()
        nivel        = request.form.get("nivel", "").strip()
        cupo         = request.form.get("cupo_maximo", "").strip()
        codigo       = request.form.get("codigo_acceso", "").strip() or None
        fecha_inicio = _parse_date(request.form.get("fecha_inicio", ""))
        fecha_fin    = _parse_date(request.form.get("fecha_fin", ""))

        cal_activas  = request.form.get("calificaciones_activas") == "on"
        cal_min      = request.form.get("calificacion_minima", "").strip()
        cal_max      = request.form.get("calificacion_maxima", "").strip()
        ayudante_ids = request.form.getlist("ayudantes")

        if not all([titulo, idioma, nivel]):
            flash("Título, idioma y nivel son obligatorios.", "danger")
            return render_template("cursos/editar_curso.html", curso=curso,
                                   profesores=profesores, ayudantes_actuales=ayudantes_actuales)

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "danger")
            return render_template("cursos/editar_curso.html", curso=curso,
                                   profesores=profesores, ayudantes_actuales=ayudantes_actuales)

        try:
            curso.titulo       = titulo
            curso.descripcion  = descripcion
            curso.idioma       = idioma
            curso.nivel        = nivel
            curso.fecha_inicio = fecha_inicio
            curso.fecha_fin    = fecha_fin
            curso.cupo_maximo  = int(cupo) if cupo else None
            curso.codigo_acceso = codigo
            curso.calificaciones_activas = cal_activas
            curso.calificacion_minima = float(cal_min) if cal_min else None
            curso.calificacion_maxima = float(cal_max) if cal_max else None

            # Actualizar ayudantes
            curso.ayudantes = []
            for aid in ayudante_ids:
                ayudante = db.session.get(Usuario, int(aid))
                if ayudante and ayudante.es_profesor and ayudante.id != curso.profesor_id:
                    curso.ayudantes.append(ayudante)

            db.session.commit()
            flash("Curso actualizado correctamente.", "success")
            return redirect(url_for("cursos.listar_cursos"))
        except Exception:
            db.session.rollback()
            flash("Error al actualizar el curso.", "danger")

    return render_template("cursos/editar_curso.html", curso=curso,
                           profesores=profesores,
                           ayudantes_actuales=ayudantes_actuales)


# ---------------------------------------------------------------------------
# Publicar / Cerrar curso
# ---------------------------------------------------------------------------

@cursos_bp.route("/<int:curso_id>/publicar", methods=["POST"])
@login_required
@profesor_required
def publicar_curso(curso_id: int):
    curso = db.session.get(Curso, curso_id)
    if not curso or not curso_propio_o_admin(curso):
        abort(403)
    if curso.estado != EstadoCurso.BORRADOR:
        flash("Solo los cursos en borrador pueden publicarse.", "warning")
        return redirect(url_for("cursos.listar_cursos"))
    curso.publicar()
    db.session.commit()
    flash(f"Curso '{curso.titulo}' publicado.", "success")
    return redirect(url_for("cursos.listar_cursos"))


@cursos_bp.route("/<int:curso_id>/cerrar", methods=["POST"])
@login_required
@profesor_required
def cerrar_curso(curso_id: int):
    curso = db.session.get(Curso, curso_id)
    if not curso or not curso_propio_o_admin(curso):
        abort(403)
    if curso.estado == EstadoCurso.CERRADO:
        flash("El curso ya está cerrado.", "info")
        return redirect(url_for("cursos.listar_cursos"))
    curso.cerrar()
    db.session.commit()
    flash(f"Curso '{curso.titulo}' cerrado.", "secondary")
    return redirect(url_for("cursos.listar_cursos"))
