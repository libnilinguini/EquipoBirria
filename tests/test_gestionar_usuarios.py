import unittest
from app import create_app, db
from app.models.models import Usuario, RolUsuario

class TestGestionUsuarios(unittest.TestCase):
    """
    Pruebas unitarias y de integración para el caso de uso: Gestionar Usuarios.
    
    Responsable del Caso de Uso: Marco Hernández
    
    Esta clase evalúa los flujos operativos del Administrador sobre las cuentas
    de los usuarios, abarcando la modificación de roles, la suspensión de cuentas,
    el manejo de errores por registros inexistentes y las restricciones de seguridad.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba (Fixture Setup).
        
        Realiza las siguientes acciones:
        1. Inicializa el entorno de pruebas de Flask con base de datos en memoria.
        2. Desactiva la validación CSRF para permitir peticiones programáticas directas.
        3. Genera el esquema de base de datos limpio.
        4. Crea dos registros base (Precondiciones):
           - Un usuario Administrador (ejecutor).
           - Un usuario Alumno (sujeto a modificaciones).
        5. Autentica al Administrador en el cliente de pruebas para los flujos normales.
        """
        # Inicialización del entorno
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Fixture 1: Creación del Administrador
        self.admin = Usuario(
            nombre="Admin", apellido="Root", 
            email="admin@sgci.com", rol=RolUsuario.ADMINISTRADOR
        )
        self.admin.set_password("admin123")
        
        # Fixture 2: Creación del Usuario de prueba (Alumno)
        self.usuario_prueba = Usuario(
            nombre="Carlos", apellido="Perez", 
            email="carlos@sgci.com", rol=RolUsuario.ALUMNO
        )
        self.usuario_prueba.set_password("pass123")
        
        # Guardar registros iniciales en la BD de pruebas
        db.session.add_all([self.admin, self.usuario_prueba])
        db.session.commit()
        
        # Autenticación por defecto como Administrador
        self.client.post('/auth/login', data={
            'email': 'admin@sgci.com',
            'password': 'admin123'
        })

    def tearDown(self):
        """
        Limpieza del entorno después de cada prueba (Fixture Teardown).
        
        Remueve las sesiones abiertas de SQLAlchemy, destruye las tablas 
        y limpia el contexto de la aplicación para evitar la contaminación de datos 
        entre ejecuciones de pruebas de forma síncrona.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_n1_asignar_rol_exitoso(self):
        """
        Escenario N-1: Actualización exitosa del rol de un usuario.
        
        Objetivo: Verificar que un administrador pueda cambiar el rol asignado
                  a una cuenta existente (ej. de ALUMNO a PROFESOR).
        
        Resultado esperado:
        - El endpoint confirma el cambio en la respuesta HTTP.
        - La base de datos actualiza el campo 'rol' al nuevo valor especificado.
        """
        # Ejecución: Envío del nuevo rol al endpoint correspondiente
        response = self.client.post(f'/admin/usuarios/{self.usuario_prueba.id}/rol', data={
            'rol': RolUsuario.PROFESOR
        }, follow_redirects=True)
        
        # Validación 1: Mensaje de confirmación en el frontend/interfaz
        self.assertIn(b'actualizado a', response.data)
        
        # Validación 2: Persistencia del cambio en la base de datos
        usuario = db.session.get(Usuario, self.usuario_prueba.id)
        self.assertEqual(usuario.rol, RolUsuario.PROFESOR, "El rol en la BD no cambió a PROFESOR.")

    def test_n2_cambio_estado_inactivo(self):
        """
        Escenario N-2: Modificación del estado de activación (Toggle) a Inactivo.
        
        Objetivo: Comprobar que el administrador pueda desactivar/suspender la cuenta
                  de un usuario que se encuentra previamente activo.
        
        Resultado esperado:
        - Se recibe un mensaje que confirma la desactivación correcta.
        - El flag 'activo' del usuario cambia a False en el backend.
        """
        # Precondición específica: Asegurar que el usuario inicia activo
        self.assertTrue(self.usuario_prueba.activo)
        
        # Ejecución: Petición de alternancia de estado (Toggle)
        response = self.client.post(f'/admin/usuarios/{self.usuario_prueba.id}/toggle', follow_redirects=True)
        
        # Validación 1: Interfaz notifica la desactivación
        self.assertIn(b'desactivado correctamente', response.data)
        
        # Validación 2: El estado lógico en la BD pasa a ser inactivo (False)
        usuario = db.session.get(Usuario, self.usuario_prueba.id)
        self.assertFalse(usuario.activo, "La cuenta del usuario debería figurar como inactiva.")

    def test_a1_usuario_no_encontrado(self):
        """
        Escenario A-1: Gestión sobre un identificador de usuario no registrado.
        
        Objetivo: Evaluar la robustez del sistema cuando se intenta modificar 
                  un ID que no existe en el universo de datos (ID: 999).
        
        Resultado esperado:
        - El sistema no rompe (no genera Error 500).
        - Retorna una respuesta controlada indicando que el usuario no fue encontrado.
        """
        # Ejecución: Intento de toggle en un ID inexistente
        response = self.client.post('/admin/usuarios/999/toggle', follow_redirects=True)
        
        # Validación: Manejo controlado de la excepción mediante respuesta visual
        self.assertIn(b'Usuario no encontrado', response.data)

    def test_e2_acceso_denegado_no_admin(self):
        """
        Escenario E-2: Control de Acceso Perimetral (RBAC) - Denegación a no-administradores.
        
        Objetivo: Asegurar que los endpoints críticos de administración estén protegidos 
                  y bloqueen a usuarios con roles inferiores (como un ALUMNO).
        
        Resultado esperado:
        - El sistema intercepta la petición a través del decorador de seguridad.
        - Se responde con un estado HTTP 403 (Forbidden) prohibiendo el acceso al panel.
        """
        # Preparación específica: Cambiar contexto de sesión de Admin a Alumno
        self.client.get('/auth/logout')
        self.client.post('/auth/login', data={
            'email': 'carlos@sgci.com',
            'password': 'pass123'
        })
        
        # Ejecución: Intento de ingreso no autorizado a la lista de usuarios
        response = self.client.get('/admin/usuarios')
        
        # Validación: Código de estado de seguridad HTTP 403 Forbidden esperado
        self.assertEqual(response.status_code, 403, "El sistema permitió el acceso a un rol no autorizado.")

if __name__ == '__main__':
    unittest.main()