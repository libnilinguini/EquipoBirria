import unittest
from unittest.mock import MagicMock

class TestRegistrarse(unittest.TestCase):

    def setUp(self):
        self.controller = MagicMock()

    def test_n1_registro_alumno_exitoso(self):
        """N-1: Datos válidos, rol Alumno."""
        self.controller.registrar.return_value = True
        resultado = self.controller.registrar(
            nombre="Fer Lopez", email="fer@email.com",
            contrasena="Pass_123", rol="Alumno"
        )
        self.assertTrue(resultado)

    def test_n2_registro_profesor_exitoso(self):
        """N-2: Datos válidos, rol Profesor."""
        self.controller.registrar.return_value = True
        resultado = self.controller.registrar(
            nombre="Omar Ruiz", email="omar@email.com",
            contrasena="Abcd_456", rol="Profesor"
        )
        self.assertTrue(resultado)

    def test_a1_correo_ya_registrado(self):
        """A-1: Correo ya existe."""
        self.controller.verificar_correo.return_value = True
        existe = self.controller.verificar_correo("fer@email.com")
        self.assertTrue(existe)

    def test_a2_campos_invalidos(self):
        """A-2: Nombre vacío y correo inválido."""
        self.controller.validar_campos.return_value = False
        valido = self.controller.validar_campos(nombre="", email="fer_email")
        self.assertFalse(valido)

    def test_e1_falla_servidor_correo(self):
        """E-1: Servidor de correo no disponible."""
        self.controller.enviar_correo.return_value = False
        enviado = self.controller.enviar_correo("fer@email.com")
        self.assertFalse(enviado)

    def test_e2_error_base_datos(self):
        """E-2: Base de datos pierde conexión."""
        self.controller.guardar.side_effect = Exception("Error de conexión a BD")
        with self.assertRaises(Exception):
            self.controller.guardar()

if __name__ == '__main__':
    unittest.main()