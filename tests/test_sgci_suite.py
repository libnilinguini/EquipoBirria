"""
Suite de pruebas integradas para el Sistema de Gestión de Cursos de Idiomas.
Equipo Birria.
"""

import unittest

# Importamos las clases de prueba que ya configuramos en los otros archivos
from tests.test_registrarse import TestRegistrarse
from tests.test_crear_curso import TestCrearCurso
from tests.test_gestionar_usuarios import TestGestionUsuarios

def suite():
    """Carga y agrupa todas las pruebas unitarias del SGCI."""
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Agregamos las pruebas al paquete
    test_suite.addTests(loader.loadTestsFromTestCase(TestRegistrarse))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCrearCurso))
    test_suite.addTests(loader.loadTestsFromTestCase(TestGestionUsuarios))
    
    return test_suite

if __name__ == '__main__':
    # Ejecutamos la suite con un nivel de detalle 2 (verbosity=2) para ver los nombres de cada prueba
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())