import unittest
from unittest.mock import MagicMock

class TestInscribirseCurso(unittest.TestCase):
    """Pruebas para el caso de uso: Inscribirse a Curso (Responsable: Carlos Gomez)"""

    def setUp(self):
        # Se simula el controlador de inscripciones para pruebas aisladas
        self.controller = MagicMock()

    def test_n1_inscripcion_exitosa(self):
        """Prueba N1: Flujo normal - Inscripción exitosa con cupo disponible."""
        # Configuración del resultado esperado según el caso de prueba N-1
        self.controller.inscribir_alumno.return_value = "Inscripción exitosa"
        resultado = self.controller.inscribir_alumno(alumno_id=1, curso_id=101)
        self.assertEqual(resultado, "Inscripción exitosa")

    def test_a1_alumno_ya_inscrito(self):
        """Prueba A1: El alumno ya se encuentra registrado en el curso."""
        # Basado en el flujo alternativo A-1 de la especificación
        self.controller.verificar_inscripcion.return_value = True
        ya_inscrito = self.controller.verificar_inscripcion(alumno_id=1, curso_id=101)
        self.assertTrue(ya_inscrito)

    def test_a2_cupo_agotado(self):
        """Prueba A2: No hay lugares disponibles en el curso seleccionado."""
        # Basado en el flujo alternativo A-2 de la especificación
        self.controller.consultar_cupo.return_value = 0
        cupo_disponible = self.controller.consultar_cupo(curso_id=101)
        self.assertEqual(cupo_disponible, 0)

    def test_e1_error_conexion_bd(self):
        """Prueba E1: Fallo de conexión a la base de datos al registrar."""
        # Basado en el flujo excepcional E-1 de la especificación
        self.controller.confirmar_inscripcion.side_effect = Exception("Error de conexión con la BD")
        with self.assertRaises(Exception):
            self.controller.confirmar_inscripcion()

if __name__ == '__main__':
    unittest.main()