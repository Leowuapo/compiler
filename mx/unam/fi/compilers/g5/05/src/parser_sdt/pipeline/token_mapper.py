"""Token mapper used by the LALR parser.

It converts lexer tokens into parser symbols, lexemes and source positions.
The mapping is unchanged from the previous syntax_parser.py implementation.
"""


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
