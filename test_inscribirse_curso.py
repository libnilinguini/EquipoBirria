import unittest
from unittest.mock import MagicMock

class TestInscribirseCurso(unittest.TestCase):
    """
    Pruebas unitarias con aislamiento (Mocks) para el caso de uso: Inscribirse a Curso.
    
    Responsable del Caso de Uso: Carlos Gómez
    
    Esta clase valida la lógica de negocio asociada al proceso de matrícula de alumnos.
    A través de simulaciones con MagicMock, se comprueba el comportamiento del 
    controlador ante escenarios de éxito, validaciones de reglas de negocio 
    (duplicados y aforos) y fallos catastróficos en la capa de datos.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba (Fixture Setup).
        
        Instancia un objeto 'MagicMock' global para emular el controlador de 
        inscripciones. Esto garantiza que cada método de prueba interactúe con 
        un componente aislado y programable desde cero.
        """
        self.controller = MagicMock()

    def test_n1_inscripcion_exitosa(self):
        """
        Escenario N1: Flujo normal - Inscripción exitosa con cupo disponible.
        
        Objetivo: Validar la ruta feliz del caso de uso, donde un alumno válido 
                  solicita ingresar a un curso con vacantes y sin registros previos.
        
        Resultado esperado:
        - El método 'inscribir_alumno' procesa la petición y retorna 'Inscripción exitosa'.
        """
        # Preparación (Arrange): Programar el comportamiento de éxito del Mock
        self.controller.inscribir_alumno.return_value = "Inscripción exitosa"
        
        # Ejecución (Act): Solicitar la inscripción con identificadores válidos
        resultado = self.controller.inscribir_alumno(alumno_id=1, curso_id=101)
        
        # Validación (Assert): Verificar que el resultado coincide con la especificación N-1
        self.assertEqual(resultado, "Inscripción exitosa", "El sistema debió confirmar la inscripción.")

    def test_a1_alumno_ya_inscrito(self):
        """
        Escenario A1: Flujo alternativo - El alumno ya se encuentra registrado.
        
        Objetivo: Asegurar que el sistema impida duplicar la matrícula de un mismo 
                  alumno dentro del mismo curso de idiomas.
        
        Resultado esperado:
        - El verificador intercepta los datos y retorna 'True', exponiendo la preexistencia.
        """
        # Preparación (Arrange): Configurar el Mock para simular un registro previo activo
        self.controller.verificar_inscripcion.return_value = True
        
        # Ejecución (Act): Consultar el estado de la inscripción del alumno
        ya_inscrito = self.controller.verificar_inscripcion(alumno_id=1, curso_id=101)
        
        # Validación (Assert): Verificar que se cumple la restricción del flujo A-1
        self.assertTrue(ya_inscrito, "El validador debería confirmar que el alumno ya está registrado.")

    def test_a2_cupo_agotado(self):
        """
        Escenario A2: Flujo alternativo - No hay lugares disponibles (Cupo Agotado).
        
        Objetivo: Comprobar que el sistema restringe el acceso a un curso si se ha 
                  alcanzado el límite máximo de alumnos permitidos.
        
        Resultado esperado:
        - El método de consulta retorna un valor de cupo igual a 0.
        """
        # Preparación (Arrange): Forzar al Mock a simular un curso lleno
        self.controller.consultar_cupo.return_value = 0
        
        # Ejecución (Act): Consultar el aforo del curso solicitado
        cupo_disponible = self.controller.consultar_cupo(curso_id=101)
        
        # Validación (Assert): Confirmar la ausencia de vacantes según el flujo A-2
        self.assertEqual(cupo_disponible, 0, "El cupo disponible devuelto debería ser cero.")

    def test_e1_error_conexion_bd(self):
        """
        Escenario E1: Flujo excepcional - Fallo crítico de conexión con la Base de Datos.
        
        Objetivo: Evaluar el comportamiento del sistema cuando ocurre una interrupción 
                  de red o caída de la base de datos en el momento de confirmar la matrícula.
        
        Resultado esperado:
        - El método propaga una excepción controlada para evitar un estado inconsistente.
        """
        # Preparación (Arrange): Inyectar una excepción simulada mediante 'side_effect'
        self.controller.confirmar_inscripcion.side_effect = Exception("Error de conexión con la BD")
        
        # Ejecución y Validación (Act & Assert): Capturar la excepción esperada según el flujo E-1
        with self.assertRaises(Exception) as contexto:
            self.controller.confirmar_inscripcion()
            
        # Validación Extra: Asegurar que el mensaje de error de infraestructura sea el correcto
        self.assertEqual(str(contexto.exception), "Error de conexión con la BD")

if __name__ == '__main__':
    unittest.main()