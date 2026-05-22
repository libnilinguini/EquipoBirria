"""
Controlador de Materiales – SGCI
Blueprint: materiales_bp  |  Prefijo: /materiales

Casos de uso cubiertos:
    - Subir material
    - Gestionar materiales  (listar, eliminar los propios)
    - Consultar materiales  (alumnos inscritos)

Equipo Birria
"""

import os
from functools import wraps
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, abort, current_app,
)
from flask_login import login_required, current_user

from app import db
from app.models.models import Material, Curso, Inscripcion, TipoMaterial, EstadoCurso

materiales_bp = Blueprint("materiales", __name__, template_folder="../templates/materiales")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extension_permitida(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def _inferir_tipo(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext in {"mp4", "avi", "mov", "mkv"}:
        return TipoMaterial.VIDEO
    if ext in {"png", "jpg", "jpeg", "gif", "webp"}:
        return TipoMaterial.IMAGEN
    if ext in {"pdf", "docx", "pptx", "txt"}:
        return TipoMaterial.DOCUMENTO
    return TipoMaterial.OTRO


# ---------------------------------------------------------------------------
# CU-MAT-01 · Subir material
# ---------------------------------------------------------------------------

@materiales_bp.route("/<int:curso_id>/subir", methods=["GET", "POST"])
@login_required
def subir_material(curso_id: int):
    """
    Permite a un Profesor subir un archivo de material didáctico a un curso.

    GET  → Formulario de carga de archivo.
    POST → Valida, guarda el archivo en disco y registra en BD.
    """
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("cursos.listar_cursos"))

    # Solo el profesor dueño o un admin puede subir materiales
    if not current_user.es_admin and curso.profesor_id != current_user.id:
        abort(403)

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        archivo = request.files.get("archivo")

        if not titulo:
            flash("El título del material es obligatorio.", "danger")
            return render_template("materiales/subir_material.html", curso=curso)

        if not archivo or archivo.filename == "":
            flash("Selecciona un archivo para subir.", "danger")
            return render_template("materiales/subir_material.html", curso=curso)

        if not _extension_permitida(archivo.filename):
            flash("Tipo de archivo no permitido.", "danger")
            return render_template("materiales/subir_material.html", curso=curso)

        nombre_seguro = secure_filename(archivo.filename)
        # Prefijo para evitar colisiones de nombres
        nombre_guardado = f"curso{curso_id}_{nombre_seguro}"
        ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_guardado)
        archivo.save(ruta)

        nuevo_material = Material(
            titulo=titulo,
            descripcion=descripcion,
            nombre_archivo=nombre_guardado,
            tipo=_inferir_tipo(nombre_seguro),
            curso_id=curso_id,
        )
        db.session.add(nuevo_material)
        db.session.commit()
        flash(f"Material '{titulo}' subido correctamente.", "success")
        return redirect(url_for("materiales.gestionar_materiales", curso_id=curso_id))

    return render_template("materiales/subir_material.html", curso=curso)


# ---------------------------------------------------------------------------
# CU-MAT-02 · Gestionar materiales
# ---------------------------------------------------------------------------

@materiales_bp.route("/<int:curso_id>/gestionar")
@login_required
def gestionar_materiales(curso_id: int):
    """
    Lista los materiales de un curso con opciones para eliminarlos.
    Solo el propietario del curso o un administrador puede gestionar.

    GET → Tabla de materiales del curso.
    """
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("cursos.listar_cursos"))

    if not current_user.es_admin and curso.profesor_id != current_user.id:
        abort(403)

    materiales = Material.query.filter_by(curso_id=curso_id).order_by(Material.fecha_subida.desc()).all()
    return render_template(
        "materiales/gestionar_materiales.html",
        curso=curso,
        materiales=materiales,
    )


@materiales_bp.route("/<int:material_id>/eliminar", methods=["POST"])
@login_required
def eliminar_material(material_id: int):
    """Elimina un material del disco y de la base de datos."""
    material = db.session.get(Material, material_id)
    if not material:
        flash("Material no encontrado.", "danger")
        return redirect(url_for("cursos.listar_cursos"))

    curso = db.session.get(Curso, material.curso_id)
    if not current_user.es_admin and curso.profesor_id != current_user.id:
        abort(403)

    # Eliminar archivo físico si existe
    ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], material.nombre_archivo)
    if os.path.exists(ruta):
        os.remove(ruta)

    db.session.delete(material)
    db.session.commit()
    flash("Material eliminado.", "secondary")
    return redirect(url_for("materiales.gestionar_materiales", curso_id=material.curso_id))


# ---------------------------------------------------------------------------
# CU-MAT-03 · Consultar materiales
# ---------------------------------------------------------------------------

@materiales_bp.route("/<int:curso_id>/consultar")
@login_required
def consultar_materiales(curso_id: int):
    """
    Muestra los materiales de un curso a los alumnos inscritos en él.

    Precondición: El alumno debe estar inscrito en el curso.

    GET → Lista de materiales disponibles para descarga.
    """
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("inscripciones.mis_inscripciones"))

    # Verificar acceso según rol
    if current_user.es_alumno:
        inscripcion = Inscripcion.query.filter_by(
            alumno_id=current_user.id, curso_id=curso_id, activa=True
        ).first()
        if not inscripcion:
            flash("Debes estar inscrito en el curso para ver sus materiales.", "warning")
            return redirect(url_for("inscripciones.cursos_disponibles"))
    elif current_user.es_profesor and curso.profesor_id != current_user.id:
        abort(403)
    elif not current_user.es_profesor and not current_user.es_admin:
        abort(403)

    materiales = Material.query.filter_by(curso_id=curso_id).order_by(Material.fecha_subida.desc()).all()
    return render_template(
        "materiales/consultar_materiales.html",
        curso=curso,
        materiales=materiales,
    )
