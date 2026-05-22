import unittest
from app import create_app, db
from app.models.models import Usuario

class TestRegistrarse(unittest.TestCase):
    def setUp(self):
        """Configuración con el patrón Application Factory."""
        # 1. Creamos la aplicación usando la fábrica de tu equipo
        self.app = create_app('testing')
        
        # 2. Forzamos la configuración para las pruebas
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # BD en memoria
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # 3. Iniciamos el cliente de pruebas y el contexto
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 4. Creamos las tablas temporales
        db.create_all()

    def tearDown(self):
        """Limpieza después de cada prueba."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_n1_registro_alumno_exitoso(self):
        """N-1: Datos válidos, rol Alumno."""
        response = self.client.post('/auth/registro', data={
            'nombre': 'Fer Lopez',
            'apellido': 'Perez',
            'email': 'fer@email.com',
            'password': 'Password_123',
            'confirmar_password': 'Password_123',
            'rol': 'alumno'
        }, follow_redirects=True)
        
        # Verificamos respuesta de éxito
        self.assertIn(b'Registro exitoso', response.data)
        
        # Verificamos en base de datos
        usuario = Usuario.query.filter_by(email='fer@email.com').first()
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.rol, 'alumno')

    def test_a1_correo_ya_registrado(self):
        """A-1: Correo ya existe."""
        # Usuario original
        self.client.post('/auth/registro', data={
            'nombre': 'Ana',
            'apellido': 'Gomez',
            'email': 'ana@email.com',
            'password': 'Password_123',
            'confirmar_password': 'Password_123',
            'rol': 'alumno'
        })
        
        # Intento duplicado
        response = self.client.post('/auth/registro', data={
            'nombre': 'Luis',
            'apellido': 'Gomez',
            'email': 'ana@email.com',
            'password': 'Password_456',
            'confirmar_password': 'Password_456',
            'rol': 'profesor'
        }, follow_redirects=True)
        
        self.assertIn(b'Este correo ya est\xc3\xa1 registrado', response.data)

    def test_a2_campos_invalidos(self):
        """A-2: Nombre vacío y contraseñas no coinciden."""
        response = self.client.post('/auth/registro', data={
            'nombre': '', 
            'apellido': 'Gomez',
            'email': 'invalido',
            'password': '123',
            'confirmar_password': '456',
            'rol': 'alumno'
        }, follow_redirects=True)
        
        self.assertIn(b'Todos los campos son obligatorios', response.data)
        self.assertIn(b'Las contrase\xc3\xb1as no coinciden', response.data)
        self.assertIn(b'La contrase\xc3\xb1a debe tener al menos 8 caracteres', response.data)

if __name__ == '__main__':
    unittest.main()