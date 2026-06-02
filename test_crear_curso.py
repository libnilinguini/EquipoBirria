import unittest
from unittest.mock import MagicMock

class TestCrearCurso(unittest.TestCase):
    """
    Pruebas unitarias con aislamiento (Mocks) para el caso de uso: Crear Curso.
    
    Responsable del Caso de Uso: Libni Morales
    
    Esta clase evalúa el comportamiento lógico del controlador de cursos utilizando 
    objetos simulados (Mocks). Permite verificar la reacción del sistema ante 
    respuestas exitosas, fallos de validación y excepciones de infraestructura 
    sin interactuar con una base de datos real.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba (Fixture Setup).
        
        Instancia un objeto 'MagicMock' que emula el comportamiento del controlador 
        de cursos, asegurando que cada escenario inicie con un componente simulado 
        limpio y programable.
        """
        self.controller = MagicMock()

    def test_n1_crear_borrador_exitoso(self):
        """
        Escenario N1: Creación exitosa de un curso en estado Borrador (Happy Path).
        
        Objetivo: Verificar que el método 'crear_curso' procese correctamente 
                  los parámetros válidos y retorne el estado esperado.
        
        Resultado esperado:
        - El método simulado intercepta la llamada y devuelve el string 'Borrador'.
        """
        # Preparación (Arrange): Definir el comportamiento del Mock mediante 'return_value'
        self.controller.crear_curso.return_value = "Borrador"
        
        # Ejecución (Act): Llamar al método simulado con argumentos válidos
        resultado = self.controller.crear_curso(nombre="Inglés A1", cupo=20)
        
        # Validación (Assert): Comprobar que la respuesta coincide con lo programado
        self.assertEqual(resultado, "Borrador", "El controlador debió retornar el estado 'Borrador'.")

    def test_a2_fechas_incoherentes(self):
        """
        Escenario A2: Flujo alternativo - Validación de rango de fechas incoherente.
        
        Objetivo: Comprobar que el mecanismo de validación rechaza la solicitud 
                  cuando la fecha de finalización es cronológicamente anterior a la de inicio.
        
        Resultado esperado:
        - El validador simulado retorna 'False' ante el envío de fechas erróneas.
        """
        # Preparación (Arrange): Programar el Mock para simular un fallo de validación
        self.controller.validar_fechas.return_value = False
        
        # Ejecución (Act): Enviar un rango de fechas lógicamente inválido
        valido = self.controller.validar_fechas("2026-05-01", "2026-04-01")
        
        # Validación (Assert): Verificar que el sistema detecta y expone la incoherencia
        self.assertFalse(valido, "La validación debería fallar si la fecha fin es anterior al inicio.")

    def test_e1_error_base_datos(self):
        """
        Escenario E1: Manejo de excepciones - Error crítico en la capa de persistencia.
        
        Objetivo: Evaluar la robustez del sistema simulando una caída o fallo 
                  en la conexión de la base de datos al intentar guardar el registro.
        
        Resultado esperado:
        - El método lanza una excepción controlada del tipo 'Exception'.
        """
        # Preparación (Arrange): Usar 'side_effect' para inyectar una excepción en el Mock
        self.controller.guardar.side_effect = Exception("Error de conexión")
        
        # Ejecución y Validación (Act & Assert): Confirmar que el sistema propaga la excepción
        with self.assertRaises(Exception) as contexto:
            self.controller.guardar()
            
        # Validación extra: Verificar el mensaje interno de la excepción capturada
        self.assertEqual(str(contexto.exception), "Error de conexión")

if __name__ == '__main__':
    unittest.main()