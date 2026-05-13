import os
import sys

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

import lexer.lector as lector
import parser_sdt.syntax_parser as parser

def main():
    while True:
        seleccion = input("Select how you will enter your code (archive/terminal): ").strip().lower()
        
        match seleccion:
            case "archive":
                try:
                    ruta = input("Enter your file path:\n")
                    tokens = lector.analizearchive(ruta)
                    if tokens:
                        print("Tokens generados exitosamente")
                        parser.analizar(tokens)
                    else:
                        print("Lexer error...")
                        
                except:
                    print("Error, invalid location")

                break

            case "terminal":
                code = input("Enter your code:\n")
                tokens = lector.analizeterminal(code)

                if tokens:
                    print("Tokens generados exitosamente")
                    parser.analizar(tokens)
                else:
                        print("Lexer error...")

                break

            case "exit":
                exit()
            case _:
                print("Error: Invalid option. Please try again.\n")

if __name__ == "__main__":
    print("Welcome to Parser & SDT from Team 5")
    main()