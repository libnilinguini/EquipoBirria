"""
Suite de pruebas integradas para el Sistema de Gestión de Cursos de Idiomas (SGCI).

Equipo de Desarrollo: Birria
Año: 2026

Este módulo actúa como el ejecutor y orquestador central (Test Runner) del sistema.
Se encarga de recolectar, agrupar y ejecutar de forma secuencial todos los bloques 
de pruebas unitarias e integradas distribuidos en el proyecto, consolidando un 
reporte unificado del estado de salud del software.
"""

import unittest

# Importación de los módulos de prueba del sistema
from tests.test_registrarse import TestRegistrarse
from tests.test_crear_curso import TestCrearCurso
from tests.test_gestionar_usuarios import TestGestionUsuarios

def suite():
    """
    Carga, empaqueta y agrupa todas las pruebas unitarias e integradas del SGCI.
    
    Utiliza el cargador por defecto de 'unittest' para extraer dinámicamente 
    los métodos de prueba dentro de cada clase seleccionada y los añade a una 
    colección centralizada (TestSuite).
    
    Returns:
        unittest.TestSuite: Un objeto contenedor que almacena la colección 
                            completa de pruebas listas para ser ejecutadas.
    """
    # Inicialización de herramientas de carga y agrupación
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Inyección de casos de uso individuales a la suite global
    test_suite.addTests(loader.loadTestsFromTestCase(TestRegistrarse))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCrearCurso))
    test_suite.addTests(loader.loadTestsFromTestCase(TestGestionUsuarios))
    
    return test_suite

if __name__ == '__main__':
    """
    Punto de entrada principal para la ejecución automatizada de pruebas.
    
    Instancia un ejecutor de texto plano (TextTestRunner) configurado con un 
    nivel de detalle alto (verbosity=2). Esto permite que la terminal imprima 
    el nombre exacto y el docstring abreviado de cada escenario de prueba 
    conforme se va ejecutando, facilitando la detección de fallos visuales de un vistazo.
    """
    # Configuración del ejecutor de pruebas con salida detallada
    runner = TextTestRunner(verbosity=2)
    runner.run(suite())