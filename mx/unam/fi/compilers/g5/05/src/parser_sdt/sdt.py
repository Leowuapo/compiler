class Nodo:
    def __init__(self, tipo, valor=None, hijos=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos else []

    def __repr__(self):
        return f"Nodo({self.tipo}, {self.valor}, {self.hijos})"


class TablaSimbolos:
    def __init__(self):
        self.simbolos = {}

    def limpiar(self):
        self.simbolos = {}

    def declarar(self, nombre, tipo):
        if nombre in self.simbolos:
            raise Exception(f"Semantic error: variable '{nombre}' already declared")
        self.simbolos[nombre] = {'tipo': tipo, 'valor': None}

    def asignar(self, nombre, valor):
        if nombre not in self.simbolos:
            raise Exception(f"Semantic error: variable '{nombre}' not declared")
        self.simbolos[nombre]['valor'] = valor

    def obtener(self, nombre):
        if nombre not in self.simbolos:
            raise Exception(f"Semantic error: variable '{nombre}' not declared")
        return self.simbolos[nombre]

    def mostrar(self):
        for nombre, datos in self.simbolos.items():
            print(f"{nombre} -> type: {datos['tipo']}, value: {datos['valor']}")


tabla_simbolos = TablaSimbolos()
ambito_pila = [tabla_simbolos]


def reset_semantica():
    """Reinicia tabla global y pila de ámbitos antes de un análisis nuevo."""
    global ambito_pila
    tabla_simbolos.limpiar()
    ambito_pila = [tabla_simbolos]


def entrar_ambito():
    """Crea un nuevo ámbito al leer '{'."""
    ambito_pila.append(TablaSimbolos())


def salir_ambito():
    """Sale del ámbito actual al leer '}'."""
    if len(ambito_pila) > 1:
        ambito_pila.pop()


def obtener_tabla_actual():
    return ambito_pila[-1]


def buscar_variable(nombre):
    for ambito in reversed(ambito_pila):
        if nombre in ambito.simbolos:
            return ambito, ambito.simbolos[nombre]
    return None, None


def evaluarexpresion(nodo):
    if nodo is None:
        raise Exception("Semantic error: invalid expression")

    if nodo.tipo == 'CONST':
        return nodo.valor

    if nodo.tipo == 'ID':
        ambito, var_info = buscar_variable(nodo.valor)
        if ambito is None:
            raise Exception(f"Semantic error: variable '{nodo.valor}' not declared")
        if var_info['valor'] is None:
            raise Exception(f"Semantic error: variable '{nodo.valor}' used before initialization")
        return var_info['valor']

    if nodo.tipo == '+':
        return evaluarexpresion(nodo.hijos[0]) + evaluarexpresion(nodo.hijos[1])

    if nodo.tipo == '-':
        return evaluarexpresion(nodo.hijos[0]) - evaluarexpresion(nodo.hijos[1])

    if nodo.tipo == '*':
        return evaluarexpresion(nodo.hijos[0]) * evaluarexpresion(nodo.hijos[1])

    if nodo.tipo == '/':
        divisor = evaluarexpresion(nodo.hijos[1])
        if divisor == 0:
            raise Exception("Semantic error: division by zero")
        return evaluarexpresion(nodo.hijos[0]) / divisor

    raise Exception(f"Unknown operator: {nodo.tipo}")


def _declarar_item(tipo_dato, item):
    """Declara un DeclItem cuando ya conocemos el TYPE."""
    nombre_var = item.valor
    expr_nodo = item.hijos[0] if item.hijos else None
    tabla_actual = obtener_tabla_actual()

    tabla_actual.declarar(nombre_var, tipo_dato)

    if expr_nodo is not None:
        valor = evaluarexpresion(expr_nodo)
        tabla_actual.asignar(nombre_var, valor)

    hijos = [Nodo('TYPE', tipo_dato)]
    if expr_nodo is not None:
        hijos.append(expr_nodo)

    return Nodo('DECL', nombre_var, hijos)


def _normalizar_lista_sentencias(nodo):
    if nodo is None:
        return []
    if isinstance(nodo, Nodo) and nodo.tipo == 'STMT_LIST':
        return nodo.hijos
    return [nodo]


def accion_semantica(num_prod, elementos):
    print(f"[DEBUG SDT] Producción: {num_prod}, elementos: {elementos}")

    # Program' → Program
    if num_prod == 0:
        return elementos[0]

    # Program → StatementList
    elif num_prod == 1:
        return Nodo('PROGRAM', None, _normalizar_lista_sentencias(elementos[0]))

    # StatementList → Statement
    elif num_prod == 2:
        return Nodo('STMT_LIST', None, _normalizar_lista_sentencias(elementos[0]))

    # StatementList → StatementList Statement
    elif num_prod == 3:
        return Nodo(
            'STMT_LIST',
            None,
            _normalizar_lista_sentencias(elementos[0]) + _normalizar_lista_sentencias(elementos[1])
        )

    # Statement → Declaration ;
    elif num_prod == 4:
        return elementos[0]

    # Statement → Assignment ;
    elif num_prod == 5:
        return elementos[0]

    # Statement → Block
    elif num_prod == 6:
        return elementos[0]

    # Declaration → TYPE DeclList
    elif num_prod == 7:
        tipo_dato = elementos[0]
        decl_items = elementos[1] if isinstance(elementos[1], list) else [elementos[1]]
        declaraciones = [_declarar_item(tipo_dato, item) for item in decl_items]
        return Nodo('DECL_LIST', tipo_dato, declaraciones)

    # DeclList → DeclItem
    elif num_prod == 8:
        return [elementos[0]]

    # DeclList → DeclList , DeclItem
    elif num_prod == 9:
        return elementos[0] + [elementos[2]]

    # DeclItem → ID
    elif num_prod == 10:
        return Nodo('DECL_ITEM', elementos[0])

    # DeclItem → ID = E
    elif num_prod == 11:
        return Nodo('DECL_ITEM', elementos[0], [elementos[2]])

    # Assignment → ID = E
    elif num_prod == 12:
        nombre_var = elementos[0]
        expr_nodo = elementos[2]
        valor = evaluarexpresion(expr_nodo)

        ambito, _ = buscar_variable(nombre_var)
        if ambito is None:
            raise Exception(f"Semantic error: variable '{nombre_var}' not declared")

        ambito.asignar(nombre_var, valor)
        return Nodo('ASSIGN', nombre_var, [expr_nodo])

    # Block → { StatementList }
    elif num_prod == 13:
        return Nodo('BLOCK', None, _normalizar_lista_sentencias(elementos[1]))

    # Block → { }
    elif num_prod == 14:
        return Nodo('BLOCK', None, [])

    # E → E + T
    elif num_prod == 15:
        return Nodo('+', None, [elementos[0], elementos[2]])

    # E → E - T
    elif num_prod == 16:
        return Nodo('-', None, [elementos[0], elementos[2]])

    # E → T
    elif num_prod == 17:
        return elementos[0]

    # T → T * F
    elif num_prod == 18:
        return Nodo('*', None, [elementos[0], elementos[2]])

    # T → T / F
    elif num_prod == 19:
        return Nodo('/', None, [elementos[0], elementos[2]])

    # T → F
    elif num_prod == 20:
        return elementos[0]

    # F → ( E )
    elif num_prod == 21:
        return elementos[1]

    # F → ID
    elif num_prod == 22:
        return Nodo('ID', elementos[0])

    # F → CONST
    elif num_prod == 23:
        val = elementos[0]
        if isinstance(val, (int, float)):
            return Nodo('CONST', val)
        if isinstance(val, str):
            try:
                val = float(val) if '.' in val else int(val)
            except ValueError:
                raise Exception(f"Semantic error: invalid constant '{val}'")
            return Nodo('CONST', val)
        raise Exception(f"Semantic error: invalid constant '{val}'")

    return None


def imprimir_arbol(nodo, nivel=0):
    if nodo is None:
        return

    sangria = "  " * nivel
    print(f"{sangria}{nodo.tipo}: {nodo.valor}")

    for hijo in nodo.hijos:
        imprimir_arbol(hijo, nivel + 1)


def exportar_arbol_graphviz(nodo, nombre_archivo="ast"):
    if nodo is None:
        print("No AST available.")
        return

    dot_path = f"{nombre_archivo}.dot"
    png_path = f"{nombre_archivo}.png"

    contador = [0]
    lineas = [
        "digraph AST {",
        '    node [shape=box, style="rounded"];'
    ]

    def recorrer(n):
        node_id = f"n{contador[0]}"
        contador[0] += 1

        etiqueta = n.tipo
        if n.valor is not None:
            etiqueta += f"\\n{n.valor}"

        lineas.append(f'    {node_id} [label="{etiqueta}"];')

        for hijo in n.hijos:
            hijo_id = recorrer(hijo)
            lineas.append(f"    {node_id} -> {hijo_id};")

        return node_id

    recorrer(nodo)
    lineas.append("}")

    with open(dot_path, "w") as archivo:
        archivo.write("\n".join(lineas))

    print(f"AST DOT generated: {dot_path}")

    try:
        import subprocess
        subprocess.run(["dot", "-Tpng", dot_path, "-o", png_path], check=True)
        print(f"AST image generated: {png_path}")
    except Exception:
        print("Graphviz image could not be generated.")
        print("You can still open the .dot file with a Graphviz viewer.")
