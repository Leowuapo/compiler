from .errors import error_semantico
from .values import ValorDesconocido, es_string_literal, es_valor_desconocido

ENTEROS = {"int", "long", "short", "unsigned"}
REALES = {"float", "double"}
VALID_TYPES = ENTEROS | REALES | {"char", "bool", "void"}

RANGOS = {
    "int": (-2147483648, 2147483647),
    "short": (-32768, 32767),
    "unsigned": (0, 4294967295),
    "long": (-9223372036854775808, 9223372036854775807),
}

def normalizar_tipo(tipo, posiciones=None, indice=0):
    if tipo not in VALID_TYPES:
        error_semantico(f"unknown type '{tipo}'", posiciones, indice)
    return tipo


def inferir_tipo_constante(valor, nodo=None):
    if es_string_literal(valor):
        return "string"

    if isinstance(valor, bool):
        return "bool"

    if isinstance(valor, int):
        return "int"

    if isinstance(valor, float):
        return "double"

    if isinstance(valor, str) and len(valor) == 1:
        return "char"

    error_semantico(f"invalid constant '{valor}'", nodo=nodo)

def tipos_convertibles(tipo_origen, tipo_destino):
    tipo_origen = normalizar_tipo(tipo_origen)
    tipo_destino = normalizar_tipo(tipo_destino)

    if tipo_destino == "void" or tipo_origen == "void":
        return tipo_origen == tipo_destino

    if tipo_origen == tipo_destino:
        return True

    if tipo_destino == "bool":
        return tipo_origen in ENTEROS | REALES | {"char", "bool"}

    if tipo_destino == "char":
        return tipo_origen in ENTEROS | {"char", "bool"}

    if tipo_destino in ENTEROS:
        return tipo_origen in ENTEROS | {"char", "bool"}

    if tipo_destino in REALES:
        return tipo_origen in ENTEROS | REALES | {"char", "bool"}

    return False


def convertir_a_tipo(valor, tipo_destino, nombre_var=None, posiciones=None, indice=0, nodo=None):
    tipo_destino = normalizar_tipo(tipo_destino, posiciones, indice)
    etiqueta = f" for variable '{nombre_var}'" if nombre_var else ""

    if es_valor_desconocido(valor):
        if not tipos_convertibles(valor.tipo, tipo_destino):
            error_semantico(
                f"cannot convert value of type '{valor.tipo}' to '{tipo_destino}'{etiqueta}",
                posiciones,
                indice,
                nodo,
            )

        return ValorDesconocido(tipo_destino, valor.descripcion)

    if tipo_destino == "bool":
        if isinstance(valor, str) and len(valor) == 1:
            return ord(valor) != 0
        return bool(valor)

    if tipo_destino == "char":
        if isinstance(valor, str) and len(valor) == 1:
            return valor
        if isinstance(valor, bool):
            valor = 1 if valor else 0
        if isinstance(valor, float):
            if not valor.is_integer():
                error_semantico(
                    f"cannot assign non-integer float to char{etiqueta}",
                    posiciones,
                    indice,
                    nodo,
                )
            valor = int(valor)
        if isinstance(valor, int) and 0 <= valor <= 255:
            return chr(valor)
        error_semantico(f"value '{valor}' out of char range{etiqueta}", posiciones, indice, nodo)

    if tipo_destino in ENTEROS:
        if isinstance(valor, str) and len(valor) == 1:
            valor = ord(valor)
        elif isinstance(valor, bool):
            valor = 1 if valor else 0
        elif isinstance(valor, float):
            if not valor.is_integer():
                error_semantico(
                    f"cannot assign non-integer value {valor} to {tipo_destino}{etiqueta}",
                    posiciones,
                    indice,
                    nodo,
                )
            valor = int(valor)

        if not isinstance(valor, int):
            error_semantico(f"cannot assign '{valor}' to {tipo_destino}{etiqueta}", posiciones, indice, nodo)

        minimo, maximo = RANGOS[tipo_destino]
        if not (minimo <= valor <= maximo):
            error_semantico(f"value {valor} out of range for {tipo_destino}{etiqueta}", posiciones, indice, nodo)
        return valor

    if tipo_destino in REALES:
        if isinstance(valor, str) and len(valor) == 1:
            valor = ord(valor)
        elif isinstance(valor, bool):
            valor = 1 if valor else 0
        if isinstance(valor, (int, float)):
            return float(valor)
        error_semantico(f"cannot assign '{valor}' to {tipo_destino}{etiqueta}", posiciones, indice, nodo)

    error_semantico(f"unsupported type '{tipo_destino}'", posiciones, indice, nodo)
