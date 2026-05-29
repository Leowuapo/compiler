# PENTA Compiler - documentación interna
# Lexer del compilador: transforma el texto fuente en una lista ordenada de tokens con línea y columna.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

import re
from .lexertable import token

# Compilamos los patrones una sola vez
compiled_tokens = [(re.compile(pattern), token_type) for pattern, token_type in token]


# Recorre el código fuente línea por línea y produce tokens con su posición exacta.
def tokenize(code):
    lista_tokens = []

    lineas = code.splitlines()

    for num_linea, linea in enumerate(lineas, start=1):
        position = 0

        while position < len(linea):
            palabra = linea[position:]
            palabraval = False

            for pattern, tipo in compiled_tokens:
                comparar = pattern.match(palabra)

                if comparar:
                    valor = comparar.group(0)

                    if tipo:
                        lista_tokens.append((tipo, valor, num_linea, position + 1))

                    position += len(valor)
                    palabraval = True
                    break

            if not palabraval:
                print(
                    f"Error: Invalid symbol at line {num_linea}, "
                    f"column {position + 1}: '{linea[position]}'"
                )
                return None

    return lista_tokens


# Lee archivos fuente usando UTF-8 y un respaldo compatible con archivos antiguos.
def _read_source_file(ruta):
    """Read source code consistently across Windows, Linux and macOS.

    UTF-8 is tried first because it is the safest default for shared projects.
    Latin-1 is kept as a fallback so older files do not crash immediately.
    """
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return archivo.read()
    except UnicodeDecodeError:
        with open(ruta, "r", encoding="latin-1") as archivo:
            return archivo.read()


# Carga un archivo y lo envía al tokenizer.
def analizearchive(ruta):
    try:
        code = _read_source_file(ruta)
        return tokenize(code)  # retornamos la lista de nuestros tokens totales

    except FileNotFoundError:
        print(f"Error, file not found in {ruta}")
        return None

    except OSError as exc:
        print(f"Error reading file '{ruta}': {exc}")
        return None


# Tokeniza código recibido directamente como cadena.
def analizeterminal(code):
    return tokenize(code)
