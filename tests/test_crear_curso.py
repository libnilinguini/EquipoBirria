import unittest
from app import create_app, db
from app.models.models import Curso, Usuario, RolUsuario

class TestCrearCurso(unittest.TestCase):
    """Pruebas para el caso de uso: Crear Curso (Responsable: Libni Morales)
       
       Esta clase agrupa los escenarios normativos y alternativos para la 
    creación de nuevos cursos dentro de la plataforma, asegurando las 
    restricciones de roles y la integridad de los datos.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba (Fixture Setup).
        
        Realiza las siguientes acciones:
        1. Inicializa la aplicación Flask en entorno de 'testing'.
        2. Configura una base de datos SQLite en memoria para aislamiento total.
        3. Desactiva la protección CSRF para facilitar las peticiones HTTP de prueba.
        4. Crea la estructura de tablas de la base de datos.
        5. Registra un usuario con rol de Profesor y simula su inicio de sesión para permitir la creación de cursos.
        """

        # Configuración del entorno de pruebas
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Cliente de pruebas y contexto de la aplicación
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Creación del esquema de la Base de Datos
        db.create_all()
        
        # Para crear un curso, necesitamos que exista un Profesor y que inicie sesión
        profesor = Usuario(
            nombre="Libni", 
            apellido="Morales", 
            email="libni@sgci.com", 
            rol=RolUsuario.PROFESOR
        )
        profesor.set_password("password123")
        db.session.add(profesor)
        db.session.commit()
        
        # Simulamos el inicio de sesión
        self.client.post('/auth/login', data={
            'email': 'libni@sgci.com',
            'password': 'password123'
        })

    def tearDown(self):
        """
        Limpieza del entorno después de cada prueba (Fixture Teardown).
        
        Remueve la sesión actual de la base de datos, destruye todas las tablas
        y destruye el contexto de la aplicación para garantizar la independencia
        entre escenarios de prueba.
        """

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_n1_crear_borrador_exitoso(self):
        """
        Escenario N1: Creación exitosa de curso en estado Borrador.
        
        Objetivo: Verificar que un profesor autenticado pueda crear un curso
                  proporcionando todos los campos requeridos válidos.
        
        Resultado esperado:
        - El controlador responde con un mensaje de éxito.
        - El registro se almacena en la base de datos con el estado inicial 'borrador'.
        """
        
        response = self.client.post('/cursos/crear', data={
            'titulo': 'Inglés A1',
            'descripcion': 'Curso básico introductorio',
            'idioma': 'Inglés',
            'nivel': 'A1',
            'cupo_maximo': 20
        }, follow_redirects=True)
        
        # Verificamos que el controlador nos devuelva el mensaje de éxito
        self.assertIn(b'creado correctamente', response.data)
        
        # Verificamos que realmente se guardó en la base de datos como borrador
        curso = Curso.query.filter_by(titulo='Inglés A1').first()
        self.assertIsNotNone(curso)
        self.assertEqual(curso.estado, 'borrador')

    def test_a2_campos_faltantes(self):
        """Prueba A2: Intento de creación sin campos obligatorios."""
        # El controlador exige titulo, idioma y nivel obligatoriamente
        response = self.client.post('/cursos/crear', data={
            'titulo': '', 
            'idioma': '',
            'nivel': ''
        }, follow_redirects=True)
        
        self.assertIn(b'T\xc3\xadtulo, idioma y nivel son obligatorios', response.data)

if __name__ == '__main__':
    unittest.main()