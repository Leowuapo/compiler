class ValorString:
    def __init__(self, valor):
        self.valor = valor

    def __repr__(self):
        return repr(self.valor)


def es_string_literal(valor):
    return isinstance(valor, ValorString)


class ValorDesconocido:
    def __init__(self, tipo, descripcion=None):
        self.tipo = tipo
        self.descripcion = descripcion

    def __repr__(self):
        if self.descripcion:
            return f"<unknown:{self.tipo}:{self.descripcion}>"
        return f"<unknown:{self.tipo}>"


def formatear_valor(valor):
    if es_valor_desconocido(valor):
        return repr(valor)

    if es_string_literal(valor):
        return repr(valor.valor)

    return repr(valor) if isinstance(valor, str) else valor


def es_valor_desconocido(valor):
    return isinstance(valor, ValorDesconocido)
