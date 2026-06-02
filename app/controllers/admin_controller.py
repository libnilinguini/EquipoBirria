"""
Controlador de Administración – SGCI
Blueprint: admin_bp  |  Prefijo: /admin

Equipo de Desarrollo: Birria
Año: 2026

Este módulo gestiona el Panel de Administración centralizado mediante un Blueprint de Flask.
Implementa el Control de Acceso Basado en Roles (RBAC) y provee los servicios web para:
    - CU-ADMIN-01: Gestión operativa de usuarios (auditoría visual y suspensión de cuentas).
    - CU-ADMIN-02: Asignación y escalamiento de privilegios/roles del sistema.
    - CU-ADMIN-03: Gobernanza del ciclo de vida de los cursos académicos.
    - CU-ADMIN-04: Monitoreo global del catálogo formativo.
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.models import Usuario, Curso, RolUsuario, EstadoCurso

# Configuración del Blueprint con aislamiento de plantillas HTML
admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


# ---------------------------------------------------------------------------
# Decorador de Autorización Perimetral
# ---------------------------------------------------------------------------

def admin_required(f):
    """
    Filtro interceptor de seguridad para control de acceso perimetral.
    
    Verifica de forma estricta que la sesión entrante pertenezca a un usuario 
    autenticado cuyo flag o propiedad de rol determine explícitamente privilegios 
    de administrador (`es_admin`).
    
    Raises:
        HTTPException: Lanza un error 403 (Forbidden) si el usuario no cumple 
                       con los criterios de acceso.
    """
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
    Renderiza el Panel de Auditoría y Control de Usuarios.
    
    Flujo:
    1. Captura parámetros de búsqueda opcionales por URL string.
    2. Modifica la consulta dinámicamente si se solicita un filtro de rol específico.
    3. Retorna la colección ordenada cronológicamente por registro.

    HTTP Methods:
        GET: Muestra la matriz de usuarios registrados.

    Query Parameters:
        rol (str): [Opcional] Filtro de búsqueda (ej. 'alumno', 'profesor').
    """
    rol_filtro = request.args.get("rol", "")
    query = Usuario.query
    
    # Validación adaptativa de la query por parámetros de URL
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
    """
    Alterna de forma atómica el estado lógico de habilitación de un usuario.
    
    Mecanismos de protección:
    - Valida la existencia del registro en la BD.
    - Bloquea intentos de auto-suspensión o suspensiones cruzadas entre administradores.

    HTTP Methods:
        POST: Aplica la mutación de estado.

    Args:
        usuario_id (int): Identificador numérico primario del usuario objetivo.
    """
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.gestionar_usuarios"))

    # Regla de Negocio: Salvaguardar cuentas raíz de administración
    if usuario.es_admin:
        flash("No es posible desactivar a otro administrador.", "warning")
        return redirect(url_for("admin.gestionar_usuarios"))

    # Conmutación lógica del estado de actividad del usuario
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
    Administra la reasignación de privilegios (Roles) a una cuenta.

    HTTP Methods:
        GET:  Muestra el formulario interactivo con el rol actual preseleccionado.
        POST: Captura la carga útil (Payload) del formulario, valida el nuevo rol 
              contra la enumeración maestra y aplica la persistencia.

    Args:
        usuario_id (int): Identificador único del usuario a reasignar.
    """
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.gestionar_usuarios"))

    if request.method == "POST":
        nuevo_rol = request.form.get("rol", "")
        # Control de Integridad: Rechazar roles que no pertenezcan al dominio
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
    """
    Gestiona la máquina de estados de un curso dentro de la plataforma.
    
    Permite transiciones controladas de publicación para que los cursos pasen de
    estados preliminares a flujos visibles o de cierre académico (borrador → publicado → cerrado).

    HTTP Methods:
        POST: Transiciona el estado del curso tras validar el payload.

    Args:
        curso_id (int): Identificador único del curso a gestionar.
    """
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
    Provee una vista analítica y global de la oferta educativa del SGCI.

    HTTP Methods:
        GET: Renderiza la tabla maestra con el cruce relacional del Curso y su Profesor.

    Query Parameters:
        estado (str): [Opcional] Filtro para segmentar por estado de ciclo académico.
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