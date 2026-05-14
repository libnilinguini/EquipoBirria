import unittest
from app import create_app, db
from app.models.models import Usuario, RolUsuario

class TestGestionUsuarios(unittest.TestCase):
    """Pruebas unitarias para el caso de uso: Gestionar Usuarios (Responsable: Marco Hernández)"""

    def setUp(self):
        """Configuración inicial: crea la app, BD temporal y dos usuarios."""
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # 1. Crear un Administrador para ejecutar las acciones
        self.admin = Usuario(
            nombre="Admin", apellido="Root", 
            email="admin@sgci.com", rol=RolUsuario.ADMINISTRADOR
        )
        self.admin.set_password("admin123")
        
        # 2. Crear un usuario de prueba (Alumno) al que le haremos modificaciones
        self.usuario_prueba = Usuario(
            nombre="Carlos", apellido="Perez", 
            email="carlos@sgci.com", rol=RolUsuario.ALUMNO
        )
        self.usuario_prueba.set_password("pass123")
        
        db.session.add_all([self.admin, self.usuario_prueba])
        db.session.commit()
        
        # Iniciar sesión como administrador
        self.client.post('/auth/login', data={
            'email': 'admin@sgci.com',
            'password': 'admin123'
        })

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_n1_asignar_rol_exitoso(self):
        """Prueba N-1: Cambiar el rol de un usuario."""
        # Carlos inicialmente es Alumno, lo cambiaremos a Profesor
        response = self.client.post(f'/admin/usuarios/{self.usuario_prueba.id}/rol', data={
            'rol': RolUsuario.PROFESOR
        }, follow_redirects=True)
        
        self.assertIn(b'actualizado a', response.data)
        
        # Verificar en BD que el cambio fue real
        usuario = db.session.get(Usuario, self.usuario_prueba.id)
        self.assertEqual(usuario.rol, RolUsuario.PROFESOR)

    def test_n2_cambio_estado_inactivo(self):
        """Prueba N-2: Desactivar cuenta de un usuario."""
        # Carlos inicialmente está activo
        self.assertTrue(self.usuario_prueba.activo)
        
        # Simulamos el clic en el botón de Activar/Desactivar
        response = self.client.post(f'/admin/usuarios/{self.usuario_prueba.id}/toggle', follow_redirects=True)
        
        self.assertIn(b'desactivado correctamente', response.data)
        
        # Verificar en BD
        usuario = db.session.get(Usuario, self.usuario_prueba.id)
        self.assertFalse(usuario.activo)

    def test_a1_usuario_no_encontrado(self):
        """Prueba A-1: Intentar cambiar estado de un ID que no existe."""
        response = self.client.post('/admin/usuarios/999/toggle', follow_redirects=True)
        self.assertIn(b'Usuario no encontrado', response.data)

    def test_e2_acceso_denegado_no_admin(self):
        """Prueba E-2: Intento de acceso por un usuario que no es admin."""
        # Cerramos la sesión del admin e iniciamos sesión como Carlos (Alumno)
        self.client.get('/auth/logout')
        self.client.post('/auth/login', data={
            'email': 'carlos@sgci.com',
            'password': 'pass123'
        })
        
        # Intentamos entrar al panel de gestión de usuarios
        response = self.client.get('/admin/usuarios')
        
        # El decorador @admin_required debe responder bloqueando el acceso (Error 403 Forbidden)
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()