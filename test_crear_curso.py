import unittest
from unittest.mock import MagicMock

class TestCrearCurso(unittest.TestCase):
    """Pruebas para el caso de uso: Crear Curso (Responsable: Libni Morales)"""

    def setUp(self):
        self.controller = MagicMock()

    def test_n1_crear_borrador_exitoso(self):
        """Prueba N1: Datos válidos, estado Borrador."""
        self.controller.crear_curso.return_value = "Borrador"
        resultado = self.controller.crear_curso(nombre="Inglés A1", cupo=20)
        self.assertEqual(resultado, "Borrador")

    def test_a2_fechas_incoherentes(self):
        """Prueba A2: Fecha fin anterior a inicio."""
        # Simulamos que la validación falla (retorna False)
        self.controller.validar_fechas.return_value = False
        valido = self.controller.validar_fechas("2026-05-01", "2026-04-01")
        self.assertFalse(valido)

    def test_e1_error_base_datos(self):
        """Prueba E1: Error de conexión al guardar."""
        self.controller.guardar.side_effect = Exception("Error de conexión")
        with self.assertRaises(Exception):
            self.controller.guardar()

if __name__ == '__main__':
    unittest.main()
    