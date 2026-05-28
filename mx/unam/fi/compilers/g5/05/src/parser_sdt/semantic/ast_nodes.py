# PENTA Compiler - documentación interna
# Nodo base del AST: estructura simple para representar tipo, valor, hijos y posición de cada elemento.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

# Estructura común para construir y recorrer el árbol de sintaxis abstracta.
class Nodo:
    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __init__(self, tipo, valor=None, hijos=None, linea=None, columna=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos else []
        self.linea = linea
        self.columna = columna

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __repr__(self):
        return f"Nodo({self.tipo}, {self.valor}, {self.hijos})"
