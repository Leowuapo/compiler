# PENTA Compiler - documentación interna
# Parser LALR con acciones semánticas: consume tokens, valida la sintaxis y coordina AST, TAC, optimización, target code y VM.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

from .parsertable import tabla_action, tabla_goto, productions
from .sdt import tabla_simbolos, tabla_funciones, accion_semantica, imprimir_arbol, exportar_arbol_graphviz, reset_semantica, entrar_ambito, salir_ambito
from backend.tac import generar_tac, imprimir_tac, guardar_tac
from backend.optimizer import optimizar_tac, imprimir_tac_optimizado, guardar_tac_optimizado
from backend.target_code import generar_target_code, imprimir_target_code, guardar_target_code
from backend.vm import ejecutar_target_code
import traceback
import os
import re
from contextlib import redirect_stdout
from io import StringIO

from .pipeline.artifacts import (
    build_artifact_paths as _build_artifact_paths,
    run_name_from_source as _run_name_from_source,
    slugify as _slugify,
)
from .pipeline.reporting import imprimir_resumen_ejecucion
from .pipeline.token_mapper import mapear_tokens

ultimo_ast = None
ultimo_resultado = None


# Ejecuta el ciclo shift/reduce y dispara acciones semánticas al reducir producciones.
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

    artifacts = _build_artifact_paths(output_dir, ast_base_path, source_path)
    ast_base_path = os.path.splitext(artifacts["ast_dot"])[0]
    output_dir = artifacts["base_dir"]

    try:
        entrada, lexemas, posiciones = mapear_tokens(tokens)
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


        accion = tabla_action.get(estado, {}).get(token)


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



# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def obtener_ultimo_resultado():
    """Devuelve el resultado detallado de la última ejecución del parser.

    Mantiene compatibilidad con el flujo anterior: analizar(tokens) sigue
    regresando True/False, pero la GUI puede consultar aquí el AST y metadatos.
    """
    return ultimo_resultado
