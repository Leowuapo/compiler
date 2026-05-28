class Nodo:
    def __init__(self, tipo, valor=None, hijos=None, linea=None, columna=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos else []
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"Nodo({self.tipo}, {self.valor}, {self.hijos})"
