from .parsertable import tabla_action, tabla_goto, productions
from .sdt import tabla_simbolos, tabla_funciones, accion_semantica, imprimir_arbol, exportar_arbol_graphviz, reset_semantica, entrar_ambito, salir_ambito
from backend.tac import generar_tac, imprimir_tac, guardar_tac
from backend.optimizer import optimizar_tac, imprimir_tac_optimizado, guardar_tac_optimizado
from backend.target_code import generar_target_code, imprimir_target_code, guardar_target_code
from backend.vm import ejecutar_target_code
import traceback
import os
from contextlib import redirect_stdout
from io import StringIO

ultimo_ast = None
ultimo_resultado = None


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

def analizar(tokens, ast_base_path="ast", output_dir=None, verbose=True, source_path=None):
    global ultimo_ast, ultimo_resultado
    ultimo_ast = None
    ultimo_resultado = {
        "ok": False,
        "fase": None,
        "error": None,
        "ast": None,
    }
    reset_semantica()

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        ast_base_path = os.path.join(output_dir, "ast")

    artifacts = {
        "ast_dot": f"{ast_base_path}.dot",
        "ast_png": f"{ast_base_path}.png",
        "tac": os.path.join(output_dir, "tac.ir") if output_dir else "tac.ir",
        "tac_optimized": os.path.join(output_dir, "tac_optimized.ir") if output_dir else "tac_optimized.ir",
        "target_code": os.path.join(output_dir, "target_code.asm") if output_dir else "target_code.asm",
    }

    try:
        entrada, lexemas, posiciones = mapear_tokens(tokens)
        #print(f"[DEBUG] Entrada (tokens): {entrada}")
        #print(f"[DEBUG] Lexemas: {lexemas}")
        #print(f"[DEBUG] Longitud de entrada: {len(entrada)}")
    except Exception as e:
        print(f"Token mapping error: {e}")
        traceback.print_exc()
        print("Parsing error...")
        ultimo_resultado = {"ok": False, "fase": "lexer/parser mapping", "error": str(e), "ast": None}
        return False

    pila = [0]
    pila_sem = []
    pila_pos = []
    pos = 0
    
    sdt_correcto = True
    sdt_error = None

    while True:
        estado = pila[-1]
        token = entrada[pos]

        #print(f"[DEBUG] Estado actual: {estado}, Token actual: '{token}', Posición: {pos}")
        #print(f"[DEBUG] Tabla ACTION para estado {estado}: {tabla_action.get(estado, {})}")

        accion = tabla_action.get(estado, {}).get(token)

        #print(f"[DEBUG] Acción encontrada: {accion}")

        if accion is None:
            linea, columna = posiciones[pos]
            esperados = list(tabla_action.get(estado, {}).keys())

            print(f"Syntax error at line {linea}, column {columna}")
            print(f"Unexpected token: '{lexemas[pos]}'")
            print(f"Expected one of: {esperados}")
            ultimo_resultado = {
                "ok": False,
                "fase": "syntax",
                "error": f"Syntax error at line {linea}, column {columna}: unexpected '{lexemas[pos]}'",
                "expected": esperados,
                "ast": None,
            }
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
            pila_pos.append(posiciones[pos])
            pos += 1

        elif accion.startswith('R'):
            num_prod = int(accion[1:])
            produccion = productions[num_prod]
            lhs, rhs = produccion
            cantidad = len(rhs)

            elementos = []
            elementos_pos = []

            for _ in range(cantidad):
                pila.pop() # pop estado
                pila.pop() # pop simbolo
                elementos.insert(0, pila_sem.pop())
                elementos_pos.insert(0, pila_pos.pop())

            try:
                resultado = accion_semantica(produccion, elementos, elementos_pos)

            except Exception as e:
                if sdt_correcto:
                    sdt_error = str(e)

                sdt_correcto = False
                resultado = None

            pila_sem.append(resultado)
            pila_pos.append(elementos_pos[0] if elementos_pos else (None, None))

            estado_expuesto = pila[-1]

            if lhs not in tabla_goto.get(estado_expuesto, {}):
                print("Parsing error...")
                ultimo_resultado = {"ok": False, "fase": "syntax", "error": "Missing GOTO transition", "ast": None}
                return False
            
            siguiente = tabla_goto[estado_expuesto][lhs]
            
            pila.append(lhs)
            pila.append(siguiente)

        elif accion == 'acc':
            if verbose:
                print("Parsing Success!")

            if sdt_correcto:
                if verbose:
                    print("SDT Verified!")
                    
                    print("Symbol table:")
                    tabla_simbolos.mostrar()

                    print("Function table:")
                    tabla_funciones.mostrar()

                    print("Parse/AST tree:")
                    imprimir_arbol(pila_sem[-1])

                ultimo_ast = pila_sem[-1]

                if verbose:
                    exportar_arbol_graphviz(ultimo_ast, ast_base_path)
                else:
                    with redirect_stdout(StringIO()):
                        exportar_arbol_graphviz(ultimo_ast, ast_base_path)

                tac = generar_tac(ultimo_ast)
                guardar_tac(tac, artifacts["tac"])

                if verbose:
                    print("TAC:")
                    imprimir_tac(tac)

                tac_optimizado = optimizar_tac(tac)
                guardar_tac_optimizado(tac_optimizado, artifacts["tac_optimized"])

                if verbose:
                    print("Optimized TAC:")
                    imprimir_tac_optimizado(tac_optimizado)

                target_code = generar_target_code(tac_optimizado)
                guardar_target_code(target_code, artifacts["target_code"])

                if verbose:
                    print("Target Code:")
                    imprimir_target_code(target_code)

                vm_resultado = None
                vm_executed = False

                if any(instr.op == "FUNC" and instr.args[0] == "main" for instr in target_code):
                    vm_executed = True
                    if verbose:
                        print("VM Execution:")
                    vm_resultado = ejecutar_target_code(
                        target_code,
                        entry_point="main",
                        mostrar_salida=verbose,
                    )
                elif verbose:
                    print("VM Execution skipped: main function not found")

                ultimo_resultado = {
                    "ok": True,
                    "fase": "semantic",
                    "error": None,
                    "ast": ultimo_ast,
                    "symbol_table": tabla_simbolos.simbolos,
                    "function_table": tabla_funciones.funciones,
                    "tac": tac,
                    "tac_optimized": tac_optimizado,
                    "target_code": target_code,
                    "vm_resultado": vm_resultado,
                    "vm_executed": vm_executed,
                    "artifacts": artifacts,
                    "source_path": source_path,
                    "output_dir": output_dir,
                }

                if not verbose:
                    imprimir_resumen_ejecucion(ultimo_resultado)

                return True
            
            else:
                print("SDT error...")
                if sdt_error:
                    print(sdt_error)
                ultimo_resultado = {
                    "ok": False,
                    "fase": "semantic",
                    "error": sdt_error,
                    "ast": pila_sem[-1] if pila_sem else None,
                }
                return False
            
        else:
            print("Parsing error...")
            return False


def imprimir_resumen_ejecucion(resultado):
    """Imprime una salida compacta para ejecuciones normales."""
    source_path = resultado.get("source_path") or "<unknown>"
    output_dir = resultado.get("output_dir") or "."
    artifacts = resultado.get("artifacts") or {}
    vm_resultado = resultado.get("vm_resultado")
    vm_executed = resultado.get("vm_executed", False)

    print("Compiler run")
    print("============")
    print(f"Input: {source_path}")
    print("Status: OK")
    print()

    print("Phases:")
    print("[OK] Lexer")
    print("[OK] Parser")
    print("[OK] Semantic analysis")
    print("[OK] AST generated")
    print("[OK] TAC generated")
    print("[OK] Optimized TAC generated")
    print("[OK] Target code generated")
    print("[OK] VM execution" if vm_executed else "[SKIP] VM execution: main function not found")
    print()

    print(f"Artifacts directory: {output_dir}")
    for label in ("ast_dot", "ast_png", "tac", "tac_optimized", "target_code"):
        path = artifacts.get(label)
        if path:
            print(f"- {path}")

    if vm_executed and vm_resultado is not None:
        print()
        print("VM Output:")
        output = vm_resultado.get("output") or []
        if output:
            for line in output:
                print(line)
        else:
            print("(no output)")
        print()
        print(f"VM Return Value: {vm_resultado.get('return_value')}")

def obtener_ultimo_resultado():
    """Devuelve el resultado detallado de la última ejecución del parser.

    Mantiene compatibilidad con el flujo anterior: analizar(tokens) sigue
    regresando True/False, pero la GUI puede consultar aquí el AST y metadatos.
    """
    return ultimo_resultado
