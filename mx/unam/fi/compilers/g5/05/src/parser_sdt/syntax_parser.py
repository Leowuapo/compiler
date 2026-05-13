from .parsertable import tabla_action, tabla_goto, productions
from .sdt import tabla_simbolos, accion_semantica, imprimir_arbol, exportar_arbol_graphviz, reset_semantica, entrar_ambito, salir_ambito
import traceback

def mapear_tokens(tokens):
    simbolos = []
    lexemas = []
    
    valid_types = {
        'int', 'float', 'double', 'char',
        'void', 'bool', 'long', 'short', 'unsigned'
    }

    for tipo, valor in tokens:
        if tipo == 'keyword' and valor in valid_types:
            simbolos.append('TYPE')
            lexemas.append(valor)

        elif tipo == 'identifier':
            simbolos.append('ID')
            lexemas.append(valor)

        elif tipo == 'constant':
            simbolos.append('CONST')
            lexemas.append(valor)

        elif tipo == 'operator' and valor == '=':
            simbolos.append('=')
            lexemas.append(valor)

        elif tipo == 'operator' and valor == '+':
            simbolos.append('+')
            lexemas.append(valor)

        elif tipo == 'operator' and valor == '-':
            simbolos.append('-')
            lexemas.append(valor)

        elif tipo == 'operator' and valor == '*':
            simbolos.append('*')
            lexemas.append(valor)

        elif tipo == 'operator' and valor == '/':
            simbolos.append('/')
            lexemas.append(valor)
        
        elif tipo == 'punctuation' and valor == ',':
            simbolos.append(',')
            lexemas.append(valor)

        elif tipo == 'punctuation' and valor == ';':
            simbolos.append(';')
            lexemas.append(valor)

        elif tipo == 'punctuation' and valor == '(':
            simbolos.append('(')
            lexemas.append(valor)

        elif tipo == 'punctuation' and valor == ')':
            simbolos.append(')')
            lexemas.append(valor)

        elif tipo == 'punctuation' and valor == '{':
            simbolos.append('{')
            lexemas.append(valor)

        elif tipo == 'punctuation' and valor == '}':
            simbolos.append('}')
            lexemas.append(valor)

        else:
            raise Exception(f"Unexpected token: {tipo} {valor}")
        
    simbolos.append('$')
    lexemas.append('$')

    return simbolos, lexemas

def analizar(tokens):
    reset_semantica()

    try:
        entrada, lexemas = mapear_tokens(tokens)
        print(f"[DEBUG] Entrada (tokens): {entrada}")
        print(f"[DEBUG] Lexemas: {lexemas}")
        print(f"[DEBUG] Longitud de entrada: {len(entrada)}")
    except Exception as e:
        print(f"Token mapping error: {e}")
        traceback.print_exc()
        print("Parsing error...")
        return False

    pila = [0]
    pila_sem = []
    pos = 0
    
    sdt_correcto = True
    sdt_error = None

    while True:
        estado = pila[-1]
        token = entrada[pos]

        print(f"[DEBUG] Estado actual: {estado}, Token actual: '{token}', Posición: {pos}")
        print(f"[DEBUG] Tabla ACTION para estado {estado}: {tabla_action.get(estado, {})}")

        accion = tabla_action.get(estado, {}).get(token)

        print(f"[DEBUG] Acción encontrada: {accion}")

        if accion is None:
            print("Parsing error...")
            return False

        if accion.startswith('S'):
            siguiente = int(accion[1:])

            if token == '{':
                entrar_ambito()
            elif token == '}':
                salir_ambito()

            pila.append(token)
            pila.append(siguiente)

            pila_sem.append(lexemas[pos])
            pos += 1

        elif accion.startswith('R'):
            num_prod = int(accion[1:])
            lhs, rhs = productions[num_prod]
            cantidad = len(rhs)

            elementos = []

            for _ in range(cantidad):
                pila.pop() # pop estado
                pila.pop() # pop simbolo
                elementos.insert(0, pila_sem.pop())

            try:
                resultado = accion_semantica(num_prod, elementos)

            except Exception as e:
                sdt_correcto = False
                sdt_error = str(e)
                resultado = None

            pila_sem.append(resultado)

            estado_expuesto = pila[-1]

            if lhs not in tabla_goto.get(estado_expuesto, {}):
                print("Parsing error...")
                return False
            
            siguiente = tabla_goto[estado_expuesto][lhs]
            
            pila.append(lhs)
            pila.append(siguiente)

        elif accion == 'acc':
            print("Parsing Success!")

            if sdt_correcto:
                print("SDT Verified!")
                
                print("Symbol table:")
                tabla_simbolos.mostrar()

                print("Parse/AST tree:")
                imprimir_arbol(pila_sem[-1])

                exportar_arbol_graphviz(pila_sem[-1], "ast")

                return True
            
            else:
                print("SDT error...")
                if sdt_error:
                    print(sdt_error)
                return False
            
        else:
            print("Parsing error...")
            return False