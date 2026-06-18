import unittest
from unittest.mock import MagicMock


class TestSubirMaterial(unittest.TestCase):
    """Pruebas para el caso de uso: Subir Material (Responsable: Romario Gonzalez)."""

    def setUp(self):
        """Configuracion inicial antes de cada prueba."""
        self.controller = MagicMock()

    def test_n1_subir_pdf_exitoso(self):
        """Prueba N-1: Archivo PDF valido de 2 MB."""
        self.controller.subir_material.return_value = {
            "subido": True,
            "mensaje": "Material subido exitosamente.",
            "archivo": "ejercicios_unidad1.pdf",
        }

        resultado = self.controller.subir_material(
            archivo="ejercicios_unidad1.pdf",
            tamanio_mb=2,
            titulo="Ejercicios Unidad 1",
            curso="Ingles A1",
        )

        self.assertTrue(resultado["subido"])
        self.assertEqual(resultado["mensaje"], "Material subido exitosamente.")
        self.assertEqual(resultado["archivo"], "ejercicios_unidad1.pdf")

    def test_n2_subir_docx_exitoso(self):
        """Prueba N-2: Archivo DOCX valido de 8 MB."""
        self.controller.subir_material.return_value = {
            "subido": True,
            "mensaje": "Material subido exitosamente.",
            "archivo": "presentacion_clase.docx",
        }

        resultado = self.controller.subir_material(
            archivo="presentacion_clase.docx",
            tamanio_mb=8,
            titulo="Presentacion clase 3",
            curso="Frances Intermedio",
        )

        self.assertTrue(resultado["subido"])
        self.assertEqual(resultado["mensaje"], "Material subido exitosamente.")
        self.assertEqual(resultado["archivo"], "presentacion_clase.docx")

    def test_a1_formato_no_permitido(self):
        """Prueba A-1: Archivo con formato no permitido."""
        self.controller.validar_formato.return_value = False
        self.controller.obtener_mensaje_error.return_value = (
            "Formato no permitido. Solo se aceptan PDF, DOCX, MP4, PNG y JPG."
        )

        formato_valido = self.controller.validar_formato("programa.exe")
        mensaje = self.controller.obtener_mensaje_error("formato")

        self.assertFalse(formato_valido)
        self.assertEqual(
            mensaje,
            "Formato no permitido. Solo se aceptan PDF, DOCX, MP4, PNG y JPG.",
        )

    def test_a2_tamanio_excedido(self):
        """Prueba A-2: Archivo mayor al limite de 50 MB."""
        self.controller.validar_tamanio.return_value = False
        self.controller.obtener_mensaje_error.return_value = (
            "El archivo excede el tamano maximo de 50 MB."
        )

        tamanio_valido = self.controller.validar_tamanio(tamanio_mb=75)
        mensaje = self.controller.obtener_mensaje_error("tamanio")

        self.assertFalse(tamanio_valido)
        self.assertEqual(mensaje, "El archivo excede el tamano maximo de 50 MB.")

    def test_e1_error_servidor_almacenamiento(self):
        """Prueba E-1: Error interno al subir el archivo al servidor."""
        self.controller.subir_archivo.side_effect = Exception(
            "No se pudo subir el material por un error interno."
        )

        with self.assertRaises(Exception):
            self.controller.subir_archivo("ejercicios_unidad1.pdf")

    def test_e2_perdida_conexion_durante_subida(self):
        """Prueba E-2: La conexion se pierde durante la subida."""
        self.controller.verificar_conexion.return_value = False
        self.controller.obtener_mensaje_error.return_value = (
            "Se interrumpio la conexion. El material no fue subido."
        )

        conexion_activa = self.controller.verificar_conexion()
        mensaje = self.controller.obtener_mensaje_error("conexion")

        self.assertFalse(conexion_activa)
        self.assertEqual(
            mensaje,
            "Se interrumpio la conexion. El material no fue subido.",
        )


if __name__ == "__main__":
    unittest.main()
