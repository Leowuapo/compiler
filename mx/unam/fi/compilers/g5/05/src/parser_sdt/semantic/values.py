# PENTA Compiler - documentación interna
# Modelos auxiliares para valores semánticos: representa strings y valores conocidos solo en tiempo de ejecución.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

# Distingue un literal string de un identificador o de un char durante el análisis semántico.
class ValorString:
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __init__(self, valor):
        self.valor = valor

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __repr__(self):
        return repr(self.valor)


# Indica si un valor representa un string literal del lenguaje.
def es_string_literal(valor):
    return isinstance(valor, ValorString)


# Marca valores cuyo tipo se conoce, pero cuyo contenido real se resolverá en ejecución.
class ValorDesconocido:
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __init__(self, tipo, descripcion=None):
        self.tipo = tipo
        self.descripcion = descripcion

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __repr__(self):
        if self.descripcion:
            return f"<unknown:{self.tipo}:{self.descripcion}>"
        return f"<unknown:{self.tipo}>"


# Prepara un valor para mostrarlo en tablas o reportes.
def formatear_valor(valor):
    if es_valor_desconocido(valor):
        return repr(valor)

    if es_string_literal(valor):
        return repr(valor.valor)

    return repr(valor) if isinstance(valor, str) else valor


# Indica si el valor solo podrá resolverse en runtime.
def es_valor_desconocido(valor):
    return isinstance(valor, ValorDesconocido)
