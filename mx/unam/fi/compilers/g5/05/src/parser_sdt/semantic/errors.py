# PENTA Compiler - documentación interna
# Errores semánticos: construye mensajes con ubicación cuando hay línea y columna disponibles.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

# Lanza un error semántico con mensaje claro y posición si está disponible.
def error_semantico(mensaje, posiciones=None, indice=0, nodo=None):
    """Lanza errores semánticos con ubicación cuando está disponible."""
    if nodo is not None and getattr(nodo, "linea", None) is not None:
        raise Exception(
            f"Semantic error at line {nodo.linea}, column {nodo.columna}: {mensaje}"
        )

    if posiciones and len(posiciones) > indice:
        linea, columna = posiciones[indice]
        if linea is not None and columna is not None:
            raise Exception(f"Semantic error at line {linea}, column {columna}: {mensaje}")

    raise Exception(f"Semantic error: {mensaje}")
