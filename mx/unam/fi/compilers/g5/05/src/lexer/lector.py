import re
from .lexertable import token              

# Compilamos los patrones una sola vez
compiled_tokens = [(re.compile(pattern), token_type) for pattern, token_type in token]

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
                        lista_tokens.append((tipo, valor))

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

def analizearchive(ruta):
    try:
        with open(ruta,'r') as archivo:
            code = archivo.read()    
    
        return tokenize(code) #retornamos la lista de nuestros tokens totales
        
    except FileNotFoundError:
        print(f"Error, file not found in {ruta}")
        return None

def analizeterminal(code):
    return tokenize(code)