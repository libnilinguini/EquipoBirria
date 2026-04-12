# Estándar de Codificación y Documentación en Python
**Sistema de Gestión de Cursos de Idiomas (SGCI) - Equipo Birria**

Para asegurar la legibilidad, mantenibilidad y calidad del código del SGCI, el equipo adopta los siguientes estándares basados en las convenciones oficiales de Python (PEP 8 y PEP 257).

## 1. Convenciones de Estilo (PEP 8)
* **Indentación:** Se utilizarán estrictamente 4 espacios por nivel de indentación nunca tabulaciones.
* **Longitud de línea:** Las líneas de código no deben exceder los 79 caracteres.
* **Espaciado:** * Dos líneas en blanco antes de definir clases o funciones principales.
    * Una línea en blanco antes de métodos dentro de una clase.
* **Imports:** Deben agruparse en el siguiente orden en la parte superior del archivo:
    1. Bibliotecas estándar de Python.
    2. Bibliotecas de terceros ej. Spring Boot si usan Jython, o frameworks como Django/Flask.
    3. Importaciones locales de la propia aplicación.

## 2. Reglas de Nomenclatura
* **Clases:** `CamelCase` (ej. `UsuarioController`, `GestionUsuariosView`).
* **Funciones y Métodos:** `snake_case` (ej. `procesar_registro()`, `validar_email()`).
* **Variables:** `snake_case` (ej. `lista_usuarios`, `correo_electronico`).
* **Constantes:** `MAYUSCULAS_CON_GUION_BAJO` (ej. `CUPO_MAXIMO`, `URL_BASE`).

## 3. Estándar de Documentación (Docstrings)
Todo módulo, clase y método público debe incluir un Docstring utilizando el formato de Google. 

**Ejemplo de documentación de un método:**
```python
def inscribir_alumno(id_alumno, id_curso):
    """
    Inscribe a un alumno en un curso validando cupos disponibles.

    Args:
        id_alumno (int): El identificador único del alumno.
        id_curso (int): El identificador único del curso.

    Returns:
        bool: True si la inscripción fue exitosa, False si no hay cupo.
    """
    pass

    ---
