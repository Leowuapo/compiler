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
