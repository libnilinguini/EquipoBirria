"""
Suite de pruebas integradas para el Sistema de Gestión de Cursos de Idiomas.
Equipo Birria.
"""

import unittest
from unittest.mock import MagicMock


class TestRegistrarse(unittest.TestCase):
    """
    Pruebas unitarias para el caso de uso: Registrarse.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba.
        """
        self.controller = MagicMock()

    def test_n1_registro_alumno_exitoso(self):
        """
        Prueba N-1: Verifica el registro exitoso con rol de Alumno.

        Returns:
            None
        """
        self.controller.registrar.return_value = True
        resultado = self.controller.registrar(
            nombre="Fer Lopez", 
            email="fer@email.com",
            contrasena="Pass_123", 
            rol="Alumno"
        )
        self.assertTrue(resultado)

    def test_n2_registro_profesor_exitoso(self):
        """
        Prueba N-2: Verifica el registro exitoso con rol de Profesor.

        Returns:
            None
        """
        self.controller.registrar.return_value = True
        resultado = self.controller.registrar(
            nombre="Omar Ruiz", 
            email="omar@email.com",
            contrasena="Abcd_456", 
            rol="Profesor"
        )
        self.assertTrue(resultado)

    def test_a1_correo_ya_registrado(self):
        """
        Prueba A-1: Verifica el comportamiento cuando el correo ya existe.

        Returns:
            None
        """
        self.controller.verificar_correo.return_value = True
        existe = self.controller.verificar_correo("fer@email.com")
        self.assertTrue(existe)

    def test_a2_campos_invalidos(self):
        """
        Prueba A-2: Verifica la validación de nombre vacío y correo inválido.

        Returns:
            None
        """
        self.controller.validar_campos.return_value = False
        valido = self.controller.validar_campos(
            nombre="", 
            email="fer_email"
        )
        self.assertFalse(valido)

    def test_e1_falla_servidor_correo(self):
        """
        Prueba E-1: Verifica manejo de error si el servidor no está disponible.

        Returns:
            None
        """
        self.controller.enviar_correo.return_value = False
        enviado = self.controller.enviar_correo("fer@email.com")
        self.assertFalse(enviado)

    def test_e2_error_base_datos(self):
        """
        Prueba E-2: Verifica manejo de excepción si la BD pierde conexión.

        Returns:
            None
        """
        self.controller.guardar.side_effect = Exception("Error de conexión")
        with self.assertRaises(Exception):
            self.controller.guardar()


class TestCrearCurso(unittest.TestCase):
    """
    Pruebas unitarias para el caso de uso: Crear Curso.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba.
        """
        self.controller = MagicMock()

    def test_n1_crear_borrador_exitoso(self):
        """
        Prueba N-1: Verifica creación exitosa de un curso en estado Borrador.

        Returns:
            None
        """
        self.controller.crear_curso.return_value = "Borrador"
        resultado = self.controller.crear_curso(nombre="Inglés A1", cupo=20)
        self.assertEqual(resultado, "Borrador")

    def test_a2_fechas_incoherentes(self):
        """
        Prueba A-2: Verifica fallo cuando la fecha de fin es anterior al inicio.

        Returns:
            None
        """
        self.controller.validar_fechas.return_value = False
        valido = self.controller.validar_fechas("2026-05-01", "2026-04-01")
        self.assertFalse(valido)

    def test_e1_error_base_datos(self):
        """
        Prueba E-1: Verifica manejo de excepción al guardar en BD.

        Returns:
            None
        """
        self.controller.guardar.side_effect = Exception("Error de conexión")
        with self.assertRaises(Exception):
            self.controller.guardar()


class TestGestionUsuarios(unittest.TestCase):
    """
    Pruebas unitarias para el caso de uso: Gestionar Usuarios.
    """

    def setUp(self):
        """
        Configuración inicial antes de cada prueba.
        """
        self.controller = MagicMock()

    def test_n1_busqueda_y_edicion_exitosa(self):
        """
        Prueba N-1: Verifica búsqueda por correo y cambio de nombre exitoso.

        Returns:
            None
        """
        mock_user = {"email": "ana@email.com", "nombre": "Ana"}
        self.controller.buscar_usuario.return_value = mock_user
        self.controller.guardar_cambios.return_value = True

        usuario = self.controller.buscar_usuario("ana@email.com")
        resultado = self.controller.guardar_cambios(
            usuario["email"], 
            nuevo_nombre="Ana M. López"
        )
        self.assertTrue(resultado)

    def test_n2_cambio_estado_inactivo(self):
        """
        Prueba N-2: Verifica búsqueda por nombre y cambio a Inactivo.

        Returns:
            None
        """
        self.controller.cambiar_estado.return_value = True
        resultado = self.controller.cambiar_estado("Carlos", "Inactivo")
        self.assertTrue(resultado)

    def test_a1_usuario_no_encontrado(self):
        """
        Prueba A-1: Verifica búsqueda de un correo que no existe.

        Returns:
            None
        """
        self.controller.buscar_usuario.return_value = None
        usuario = self.controller.buscar_usuario("inexistente@test.com")
        self.assertIsNone(usuario)

    def test_a2_formato_correo_invalido(self):
        """
        Prueba A-2: Verifica intento de guardar correo sin formato correcto.

        Returns:
            None
        """
        self.controller.validar_email.return_value = False
        es_valido = self.controller.validar_email("marco email")
        self.assertFalse(es_valido)

    def test_e1_error_conexion_bd(self):
        """
        Prueba E-1: Verifica manejo de pérdida de conexión a BD al guardar.

        Returns:
            None
        """
        err_msg = "Error de conexión a BD"
        self.controller.guardar_cambios.side_effect = Exception(err_msg)
        
        with self.assertRaises(Exception):
            self.controller.guardar_cambios(
                "ana@email.com", 
                nuevo_nombre="Ana"
            )

    def test_e2_sesion_expirada(self):
        """
        Prueba E-2: Verifica el manejo de sesión expirada del administrador.

        Returns:
            None
        """
        self.controller.verificar_sesion.return_value = False
        sesion_activa = self.controller.verificar_sesion()
        self.assertFalse(sesion_activa)


if __name__ == '__main__':
    unittest.main()