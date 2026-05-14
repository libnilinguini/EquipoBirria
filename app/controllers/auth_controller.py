"""
Controlador de Autenticación – SGCI
Blueprint: auth_bp  |  Prefijo: /auth

Casos de uso cubiertos:
    - Registrarse
    - Iniciar sesión
    - Cerrar sesión

Equipo Birria
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.models import Usuario, RolUsuario

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


# ---------------------------------------------------------------------------
# CU-AUTH-01 · Registrarse
# ---------------------------------------------------------------------------

@auth_bp.route("/registro", methods=["GET", "POST"])
def register():
    """
    Permite a un Alumno o Profesor registrarse en el SGCI.

    GET  → Muestra el formulario de registro.
    POST → Valida los datos, crea el usuario y redirige al login.
    """
    if current_user.is_authenticated:
        return redirect(url_for("cursos.listar_cursos"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar_password", "")
        rol = request.form.get("rol", RolUsuario.ALUMNO)

        # Validaciones básicas
        errores = []
        if not all([nombre, apellido, email, password, confirmar]):
            errores.append("Todos los campos son obligatorios.")
        if password != confirmar:
            errores.append("Las contraseñas no coinciden.")
        if len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if rol not in [RolUsuario.ALUMNO, RolUsuario.PROFESOR]:
            errores.append("Rol no válido.")
        if Usuario.query.filter_by(email=email).first():
            errores.append("Este correo ya está registrado.")

        if errores:
            for error in errores:
                flash(error, "danger")
            return render_template("auth/register.html", form_data=request.form)

        nuevo_usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            email=email,
            rol=rol,
        )
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro exitoso. Por favor inicia sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form_data={})


# ---------------------------------------------------------------------------
# CU-AUTH-02 · Iniciar sesión
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Autentica al usuario con email y contraseña.

    GET  → Muestra el formulario de inicio de sesión.
    POST → Verifica credenciales y establece la sesión.
    """
    if current_user.is_authenticated:
        return redirect(url_for("cursos.listar_cursos"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        recordar = request.form.get("recordar") == "on"

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.check_password(password):
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template("auth/login.html")

        if not usuario.activo:
            flash("Tu cuenta está desactivada. Contacta al administrador.", "warning")
            return render_template("auth/login.html")

        login_user(usuario, remember=recordar)
        flash(f"Bienvenido, {usuario.nombre_completo}.", "success")

        next_page = request.args.get("next")
        return redirect(next_page or url_for("cursos.listar_cursos"))

    return render_template("auth/login.html")


# ---------------------------------------------------------------------------
# CU-AUTH-03 · Cerrar sesión
# ---------------------------------------------------------------------------

@auth_bp.route("/logout")
@login_required
def logout():
    """Cierra la sesión activa del usuario y redirige al login."""
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))
