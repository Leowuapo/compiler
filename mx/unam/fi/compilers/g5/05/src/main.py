# PENTA Compiler - documentación interna
# Punto de entrada por terminal: recibe código fuente, ejecuta lexer/parser y guarda los artefactos de compilación.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

import argparse
import os
import re
import sys

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

import lexer.lector as lector
import parser_sdt.syntax_parser as parser

OUTPUTS_ROOT = os.path.join(SRC_ROOT, "outputs")


# Convierte nombres de archivos o corridas en identificadores seguros para rutas.
def _slugify(value):
    value = str(value or "run")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    value = value.strip("._")
    return value or "run"


# Construye una carpeta de salida estable a partir del archivo o de una etiqueta de ejecución.
def _default_output_dir(source_path=None, label="terminal_session"):
    if source_path:
        base = os.path.splitext(os.path.basename(source_path))[0]
    else:
        base = label

    return os.path.join(OUTPUTS_ROOT, _slugify(base))


# Valida que el lexer produjo tokens y entrega la secuencia al parser.
def _compile_tokens(tokens, *, source_path=None, output_dir=None, verbose=False):
    if not tokens:
        print("Lexer error...")
        return False

    if verbose:
        print("Tokens generated successfully")

    return parser.analizar(
        tokens,
        output_dir=output_dir,
        verbose=verbose,
        source_path=source_path,
    )


# Compila un archivo fuente y guarda los resultados en la carpeta de salida correspondiente.
def compile_file(source_path, *, output_dir=None, verbose=False):
    output_dir = output_dir or _default_output_dir(source_path)
    tokens = lector.analizearchive(source_path)
    return _compile_tokens(
        tokens,
        source_path=source_path,
        output_dir=output_dir,
        verbose=verbose,
    )


# Compila código recibido como texto directo desde terminal o desde pruebas automatizadas.
def compile_terminal(code, *, output_dir=None, verbose=False):
    output_dir = output_dir or _default_output_dir(label="terminal_session")
    tokens = lector.analizeterminal(code)
    return _compile_tokens(
        tokens,
        source_path="<terminal>",
        output_dir=output_dir,
        verbose=verbose,
    )


# Permite elegir entrada por archivo o por terminal cuando no se pasa una ruta directa.
def interactive_mode(*, output_dir=None, verbose=False):
    while True:
        seleccion = input("Select how you will enter your code (archive/terminal): ").strip().lower()

        match seleccion:
            case "archive":
                try:
                    ruta = input("Enter your file path:\n").strip()
                    return compile_file(ruta, output_dir=output_dir, verbose=verbose)
                except Exception as e:
                    print(f"Internal error: {e}")
                    if verbose:
                        import traceback
                        traceback.print_exc()
                    return False

            case "terminal":
                code = input("Enter your code:\n")
                return compile_terminal(code, output_dir=output_dir, verbose=verbose)

            case "exit":
                return False

            case _:
                print("Error: Invalid option. Please try again.\n")


# Define los argumentos disponibles para usar el compilador desde consola.
def parse_args():
    arg_parser = argparse.ArgumentParser(
        description="Compile a source file or terminal input with the Team 5 compiler."
    )
    arg_parser.add_argument(
        "source",
        nargs="?",
        help="Path to the source file to compile. If omitted, interactive mode is used.",
    )
    arg_parser.add_argument(
        "-o",
        "--output-dir",
        help="Directory where generated artifacts will be stored.",
    )
    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print full AST, TAC, optimized TAC and target code in the console.",
    )
    arg_parser.add_argument(
        "--terminal",
        action="store_true",
        help="Read source code directly from terminal input.",
    )
    return arg_parser.parse_args()


# Coordina el modo de ejecución cuando el archivo se llama desde terminal.
def main():
    args = parse_args()

    print("Welcome to Parser & SDT from Team 5")

    if args.terminal:
        code = input("Enter your code:\n")
        return compile_terminal(code, output_dir=args.output_dir, verbose=args.verbose)

    if args.source:
        return compile_file(args.source, output_dir=args.output_dir, verbose=args.verbose)

    return interactive_mode(output_dir=args.output_dir, verbose=args.verbose)


if __name__ == "__main__":
    main()
