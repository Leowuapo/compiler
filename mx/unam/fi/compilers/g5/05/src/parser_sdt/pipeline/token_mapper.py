# PENTA Compiler - documentación interna
# Adaptador entre lexer y parser: convierte tokens crudos en símbolos terminales entendidos por la tabla LALR.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

"""Mapeo entre tokens del lexer y símbolos terminales del parser."""


# Traduce la salida del lexer al vocabulario de terminales usado por el parser LALR.
def mapear_tokens(tokens):
    simbolos = []
    lexemas = []
    posiciones = []

    valid_types = {
        'int', 'float', 'double', 'char',
        'void', 'bool', 'long', 'short', 'unsigned'
    }

    for tipo, valor, linea, columna in tokens:
        if tipo == 'keyword' and valor in valid_types:
            simbolos.append('TYPE')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'keyword' and valor == 'main':
            simbolos.append('ID')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'keyword' and valor in {
            'if', 'else', 'while', 'for',
            'switch', 'case', 'default',
            'break', 'continue', 'return',
            'print', 'printf'
        }:
            simbolos.append(valor)
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'identifier' and valor in {'true', 'false'}:
            simbolos.append('CONST')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'identifier':
            simbolos.append('ID')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'constant':
            simbolos.append('CONST')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'literal':
            simbolos.append('CONST')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'operator' and valor in {
            '=', '+', '-', '*', '/', '%',
            '&&', '||', '!',
            '==', '!=', '<', '>', '<=', '>=',
            '++', '--'
        }:
            simbolos.append(valor)
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == ',':
            simbolos.append(',')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == ';':
            simbolos.append(';')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == '(':
            simbolos.append('(')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == ')':
            simbolos.append(')')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == '{':
            simbolos.append('{')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == '}':
            simbolos.append('}')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == '[':
            simbolos.append('[')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == ']':
            simbolos.append(']')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        elif tipo == 'punctuation' and valor == ':':
            simbolos.append(':')
            lexemas.append(valor)
            posiciones.append((linea, columna))

        else:
            raise Exception(f"Unexpected token: {tipo} {valor}")

    simbolos.append('$')
    lexemas.append('$')

    posiciones.append((None, None))
    return simbolos, lexemas, posiciones
