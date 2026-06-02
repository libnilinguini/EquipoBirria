import unittest
from app import create_app, db
from app.models.models import Usuario

class TestRegistrarse(unittest.TestCase):
    """
    Pruebas unitarias y de integración para el caso de uso: Registrarse.
    
    Esta clase valida el flujo de creación de nuevas cuentas en el sistema,
    garantizando que se cumplan las reglas de negocio de la capa de autenticación,
    tales como la validación de contraseñas seguras, unicidad de correos y campos obligatorios.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba (Fixture Setup).
        
        Aplica el patrón Application Factory para construir una instancia aislada
        de la aplicación en modo de pruebas, levanta una base de datos SQLite 
        completamente limpia en memoria y desactiva CSRF para permitir llamadas POST directas.
        """
        # 1. Creación de la aplicación bajo entorno de prueba
        self.app = create_app('testing')
        
        # 2. Forzado de flags de configuración
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # 3. Inicialización del cliente HTTP y el contexto de aplicación Flask
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 4. Generación del esquema de tablas temporal
        db.create_all()

    def tearDown(self):
        """
        Limpieza del entorno después de cada prueba (Fixture Teardown).
        
        Garantiza que la sesión de la base de datos se cierre por completo,
        destruye las tablas en memoria y retira el contexto de la aplicación 
        para dejar el entorno listo para el siguiente escenario.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_n1_registro_alumno_exitoso(self):
        """
        Escenario N-1: Registro exitoso de un nuevo usuario con rol Alumno.
        
        Objetivo: Evaluar el camino feliz donde un aspirante envía todos sus 
                  datos correctamente estructurados y válidos.
        
        Resultado esperado:
        - El sistema responde con una notificación de éxito ('Registro exitoso').
        - El registro se inserta físicamente en la BD conservando el rol asignado.
        """
        # Ejecución: Envío de formulario de registro correcto
        response = self.client.post('/auth/registro', data={
            'nombre': 'Fer Lopez',
            'apellido': 'Perez',
            'email': 'fer@email.com',
            'password': 'Password_123',
            'confirmar_password': 'Password_123',
            'rol': 'alumno'
        }, follow_redirects=True)
        
        # Validación 1: Confirmación de interfaz/cliente
        self.assertIn(b'Registro exitoso', response.data)
        
        # Validación 2: Persistencia y mapeo correcto en la Base de Datos
        usuario = Usuario.query.filter_by(email='fer@email.com').first()
        self.assertIsNotNone(usuario, "El usuario debería haberse registrado en la BD.")
        self.assertEqual(usuario.rol, 'alumno', "El rol guardado no coincide con el solicitado.")

    def test_a1_correo_ya_registrado(self):
        """
        Escenario A-1: Intento de registro utilizando un email preexistente.
        
        Objetivo: Asegurar que el sistema no permita la duplicidad de cuentas 
                  bajo la misma dirección de correo electrónico.
        
        Resultado esperado:
        - El sistema bloquea el segundo registro.
        - Se envía un mensaje de advertencia indicando que el correo ya está en uso.
        """
        # Preparación: Registrar un usuario inicial de control
        self.client.post('/auth/registro', data={
            'nombre': 'Ana',
            'apellido': 'Gomez',
            'email': 'ana@email.com',
            'password': 'Password_123',
            'confirmar_password': 'Password_123',
            'rol': 'alumno'
        })
        
        # Ejecución: Intento de registrar un segundo usuario con el mismo email (ana@email.com)
        response = self.client.post('/auth/registro', data={
            'nombre': 'Luis',
            'apellido': 'Gomez',
            'email': 'ana@email.com',
            'password': 'Password_456',
            'confirmar_password': 'Password_456',
            'rol': 'profesor'
        }, follow_redirects=True)
        
        # Validación: Captura del mensaje de error controlado (Manejo de codificación para 'está')
        self.assertIn(b'Este correo ya est\xc3\xa1 registrado', response.data)

    def test_a2_campos_invalidos(self):
        """
        Escenario A-2: Envío masivo de datos inválidos en el formulario.
        
        Objetivo: Comprobar la robustez de las validaciones del formulario al recibir 
                  múltiples errores simultáneos (campos vacíos, passwords que no coinciden 
                  y longitud insegura).
        
        Resultado esperado:
        - La petición es rechazada de inmediato.
        - El sistema es capaz de acumular e informar todos los errores correspondientes en la respuesta.
        """
        # Ejecución: Envío de datos intencionalmente erróneos
        response = self.client.post('/auth/registro', data={
            'nombre': '', 
            'apellido': 'Gomez',
            'email': 'invalido',
            'password': '123',
            'confirmar_password': '456',
            'rol': 'alumno'
        }, follow_redirects=True)
        
        # Validación: Verificación de la presencia de cada regla de negocio violada
        self.assertIn(b'Todos los campos son obligatorios', response.data)
        self.assertIn(b'Las contrase\xc3\xb1as no coinciden', response.data)
        self.assertIn(b'La contrase\xc3\xb1a debe tener al menos 8 caracteres', response.data)

if __name__ == '__main__':
    unittest.main()