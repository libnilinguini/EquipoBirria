"""
Controlador de Administración – SGCI
Blueprint: admin_bp  |  Prefijo: /admin

Casos de uso cubiertos:
    - Gestionar usuarios   (listar, activar/desactivar)
    - Asignar roles
    - Cambiar estado del curso
    - Consultar cursos

Equipo Birria
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.models import Usuario, Curso, RolUsuario, EstadoCurso

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


# ---------------------------------------------------------------------------
# Decorador de autorización para administradores
# ---------------------------------------------------------------------------

def admin_required(f):
    """Restringe el acceso exclusivamente a usuarios con rol Administrador."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# CU-ADMIN-01 · Gestionar usuarios
# ---------------------------------------------------------------------------

@admin_bp.route("/usuarios")
@login_required
@admin_required
def gestionar_usuarios():
    """
    Lista todos los usuarios del sistema con opciones para activar/desactivar.

    GET → Muestra la tabla de usuarios con filtros opcionales.
    """
    rol_filtro = request.args.get("rol", "")
    query = Usuario.query
    if rol_filtro and rol_filtro in RolUsuario.TODOS:
        query = query.filter_by(rol=rol_filtro)

    usuarios = query.order_by(Usuario.fecha_registro.desc()).all()
    return render_template(
        "admin/gestionar_usuarios.html",
        usuarios=usuarios,
        roles=RolUsuario.TODOS,
        rol_filtro=rol_filtro,
    )


@admin_bp.route("/usuarios/<int:usuario_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_usuario(usuario_id: int):
    """Activa o desactiva la cuenta de un usuario."""
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.gestionar_usuarios"))

    if usuario.es_admin:
        flash("No es posible desactivar a otro administrador.", "warning")
        return redirect(url_for("admin.gestionar_usuarios"))

    usuario.activo = not usuario.activo
    db.session.commit()
    estado = "activado" if usuario.activo else "desactivado"
    flash(f"Usuario {usuario.nombre_completo} {estado} correctamente.", "success")
    return redirect(url_for("admin.gestionar_usuarios"))


# ---------------------------------------------------------------------------
# CU-ADMIN-02 · Asignar roles
# ---------------------------------------------------------------------------

@admin_bp.route("/usuarios/<int:usuario_id>/rol", methods=["GET", "POST"])
@login_required
@admin_required
def asignar_rol(usuario_id: int):
    """
    Cambia el rol de un usuario existente.

    GET  → Muestra formulario de selección de rol.
    POST → Aplica el nuevo rol y guarda los cambios.
    """
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.gestionar_usuarios"))

    if request.method == "POST":
        nuevo_rol = request.form.get("rol", "")
        if nuevo_rol not in RolUsuario.TODOS:
            flash("Rol no válido.", "danger")
        else:
            usuario.rol = nuevo_rol
            db.session.commit()
            flash(f"Rol de {usuario.nombre_completo} actualizado a '{nuevo_rol}'.", "success")
            return redirect(url_for("admin.gestionar_usuarios"))

    return render_template(
        "admin/asignar_rol.html",
        usuario=usuario,
        roles=RolUsuario.TODOS,
    )


# ---------------------------------------------------------------------------
# CU-ADMIN-03 · Cambiar estado del curso
# ---------------------------------------------------------------------------

@admin_bp.route("/cursos/<int:curso_id>/estado", methods=["POST"])
@login_required
@admin_required
def cambiar_estado_curso(curso_id: int):
    """Cambia el estado de un curso (borrador → publicado → cerrado)."""
    curso = db.session.get(Curso, curso_id)
    if not curso:
        flash("Curso no encontrado.", "danger")
        return redirect(url_for("admin.consultar_cursos"))

    nuevo_estado = request.form.get("estado", "")
    if nuevo_estado not in EstadoCurso.TODOS:
        flash("Estado no válido.", "danger")
    else:
        curso.estado = nuevo_estado
        db.session.commit()
        flash(f"Estado del curso '{curso.titulo}' cambiado a '{nuevo_estado}'.", "success")

    return redirect(url_for("admin.consultar_cursos"))


# ---------------------------------------------------------------------------
# CU-ADMIN-04 · Consultar cursos
# ---------------------------------------------------------------------------

@admin_bp.route("/cursos")
@login_required
@admin_required
def consultar_cursos():
    """
    Muestra todos los cursos del sistema con su estado y datos del profesor.

    GET → Tabla de cursos con filtro por estado.
    """
    estado_filtro = request.args.get("estado", "")
    query = Curso.query
    if estado_filtro and estado_filtro in EstadoCurso.TODOS:
        query = query.filter_by(estado=estado_filtro)

    cursos = query.order_by(Curso.fecha_creacion.desc()).all()
    return render_template(
        "admin/consultar_cursos.html",
        cursos=cursos,
        estados=EstadoCurso.TODOS,
        estado_filtro=estado_filtro,
    )
