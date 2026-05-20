class Nodo:
    def __init__(self, tipo, valor=None, hijos=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos else []

    def __repr__(self):
        return f"Nodo({self.tipo}, {self.valor}, {self.hijos})"


ENTEROS = {"int", "long", "short", "unsigned"}
REALES = {"float", "double"}
VALID_TYPES = ENTEROS | REALES | {"char", "bool", "void"}

RANGOS = {
    "int": (-2147483648, 2147483647),
    "short": (-32768, 32767),
    "unsigned": (0, 4294967295),
    "long": (-9223372036854775808, 9223372036854775807),
}


class TablaSimbolos:
    def __init__(self):
        self.simbolos = {}

    def limpiar(self):
        self.simbolos = {}

    def declarar(self, nombre, tipo):
        tipo = normalizar_tipo(tipo)
        if tipo == "void":
            raise Exception(f"Semantic error: variable '{nombre}' cannot be declared as void")
        if nombre in self.simbolos:
            raise Exception(f"Semantic error: variable '{nombre}' already declared")
        self.simbolos[nombre] = {'tipo': tipo, 'valor': None}

    def asignar(self, nombre, valor):
        if nombre not in self.simbolos:
            raise Exception(f"Semantic error: variable '{nombre}' not declared")
        tipo_destino = self.simbolos[nombre]['tipo']
        self.simbolos[nombre]['valor'] = convertir_a_tipo(valor, tipo_destino, nombre)

    def obtener(self, nombre):
        if nombre not in self.simbolos:
            raise Exception(f"Semantic error: variable '{nombre}' not declared")
        return self.simbolos[nombre]

    def mostrar(self):
        for nombre, datos in self.simbolos.items():
            valor = datos['valor']
            if isinstance(valor, str):
                valor = repr(valor)
            print(f"{nombre} -> type: {datos['tipo']}, value: {valor}")


tabla_simbolos = TablaSimbolos()
ambito_pila = [tabla_simbolos]


def reset_semantica():
    global ambito_pila
    tabla_simbolos.limpiar()
    ambito_pila = [tabla_simbolos]


def entrar_ambito():
    ambito_pila.append(TablaSimbolos())


def salir_ambito():
    if len(ambito_pila) > 1:
        ambito_pila.pop()


def obtener_tabla_actual():
    return ambito_pila[-1]


def buscar_variable(nombre):
    for ambito in reversed(ambito_pila):
        if nombre in ambito.simbolos:
            return ambito, ambito.simbolos[nombre]
    return None, None


def normalizar_tipo(tipo):
    if tipo not in VALID_TYPES:
        raise Exception(f"Semantic error: unknown type '{tipo}'")
    return tipo


def inferir_tipo_constante(valor):
    if isinstance(valor, bool):
        return "bool"
    if isinstance(valor, int):
        return "int"
    if isinstance(valor, float):
        return "double"
    if isinstance(valor, str) and len(valor) == 1:
        return "char"
    raise Exception(f"Semantic error: invalid constant '{valor}'")


def valor_numerico(valor):
    if isinstance(valor, bool):
        return 1 if valor else 0
    if isinstance(valor, str) and len(valor) == 1:
        return ord(valor)
    return valor


def convertir_a_tipo(valor, tipo_destino, nombre_var=None):
    tipo_destino = normalizar_tipo(tipo_destino)
    etiqueta = f" for variable '{nombre_var}'" if nombre_var else ""

    if tipo_destino == "bool":
        if isinstance(valor, str) and len(valor) == 1:
            return ord(valor) != 0
        return bool(valor)

    if tipo_destino == "char":
        if isinstance(valor, str) and len(valor) == 1:
            return valor
        if isinstance(valor, bool):
            valor = 1 if valor else 0
        if isinstance(valor, float):
            if not valor.is_integer():
                raise Exception(f"Semantic error: cannot assign non-integer float to char{etiqueta}")
            valor = int(valor)
        if isinstance(valor, int) and 0 <= valor <= 255:
            return chr(valor)
        raise Exception(f"Semantic error: value '{valor}' out of char range{etiqueta}")

    if tipo_destino in ENTEROS:
        if isinstance(valor, str) and len(valor) == 1:
            valor = ord(valor)
        elif isinstance(valor, bool):
            valor = 1 if valor else 0
        elif isinstance(valor, float):
            if not valor.is_integer():
                raise Exception(f"Semantic error: cannot assign non-integer value {valor} to {tipo_destino}{etiqueta}")
            valor = int(valor)

        if not isinstance(valor, int):
            raise Exception(f"Semantic error: cannot assign '{valor}' to {tipo_destino}{etiqueta}")

        minimo, maximo = RANGOS[tipo_destino]
        if not (minimo <= valor <= maximo):
            raise Exception(f"Semantic error: value {valor} out of range for {tipo_destino}{etiqueta}")
        return valor

    if tipo_destino in REALES:
        if isinstance(valor, str) and len(valor) == 1:
            valor = ord(valor)
        elif isinstance(valor, bool):
            valor = 1 if valor else 0
        if isinstance(valor, (int, float)):
            return float(valor)
        raise Exception(f"Semantic error: cannot assign '{valor}' to {tipo_destino}{etiqueta}")

    raise Exception(f"Semantic error: unsupported type '{tipo_destino}'")


def tipo_aritmetico(tipo_izq, tipo_der, operador):
    # En C, char y bool se promocionan a int en expresiones aritméticas.
    if tipo_izq in {"double"} or tipo_der in {"double"}:
        return "double"
    if tipo_izq in {"float"} or tipo_der in {"float"}:
        return "float"
    return "int"


def evaluarexpresion(nodo, con_tipo=False):
    valor, tipo = evaluar_con_tipo(nodo)
    return (valor, tipo) if con_tipo else valor


def evaluar_con_tipo(nodo):
    if nodo is None:
        raise Exception("Semantic error: invalid expression")

    if nodo.tipo == 'CONST':
        return nodo.valor, inferir_tipo_constante(nodo.valor)

    if nodo.tipo == 'ID':
        ambito, var_info = buscar_variable(nodo.valor)
        if ambito is None:
            raise Exception(f"Semantic error: variable '{nodo.valor}' not declared")
        if var_info['valor'] is None:
            raise Exception(f"Semantic error: variable '{nodo.valor}' used before initialization")
        return var_info['valor'], var_info['tipo']

    if nodo.tipo in {'+', '-', '*', '/'}:
        izq, tipo_izq = evaluar_con_tipo(nodo.hijos[0])
        der, tipo_der = evaluar_con_tipo(nodo.hijos[1])
        izq_num = valor_numerico(izq)
        der_num = valor_numerico(der)
        tipo_res = tipo_aritmetico(tipo_izq, tipo_der, nodo.tipo)

        if nodo.tipo == '+':
            valor = izq_num + der_num
        elif nodo.tipo == '-':
            valor = izq_num - der_num
        elif nodo.tipo == '*':
            valor = izq_num * der_num
        else:
            if der_num == 0:
                raise Exception("Semantic error: division by zero")
            if tipo_res == "int":
                valor = int(izq_num / der_num)  # división entera estilo C, truncada hacia 0
            else:
                valor = izq_num / der_num

        if tipo_res == "int":
            valor = int(valor)
        else:
            valor = float(valor)
        return valor, tipo_res

    raise Exception(f"Unknown operator: {nodo.tipo}")


def _declarar_item(tipo_dato, item):
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


def parsear_constante(val):
    if isinstance(val, (int, float, bool)):
        return val
    if isinstance(val, str):
        if val == "true":
            return True
        if val == "false":
            return False
        if len(val) >= 2 and val[0] == "'" and val[-1] == "'":
            contenido = val[1:-1]
            escapes = {"\\n": "\n", "\\t": "\t", "\\r": "\r", "\\0": "\0", "\\'": "'", "\\\\": "\\"}
            contenido = escapes.get(contenido, contenido)
            if len(contenido) != 1:
                raise Exception(f"Semantic error: invalid char literal {val}")
            return contenido
        try:
            return float(val) if '.' in val else int(val)
        except ValueError:
            raise Exception(f"Semantic error: invalid constant '{val}'")
    raise Exception(f"Semantic error: invalid constant '{val}'")


def accion_semantica(num_prod, elementos):
    #print(f"[DEBUG SDT] Producción: {num_prod}, elementos: {elementos}")

    if num_prod == 0:
        return elementos[0]
    elif num_prod == 1:
        return Nodo('PROGRAM', None, _normalizar_lista_sentencias(elementos[0]))
    elif num_prod == 2:
        return Nodo('STMT_LIST', None, _normalizar_lista_sentencias(elementos[0]))
    elif num_prod == 3:
        return Nodo('STMT_LIST', None, _normalizar_lista_sentencias(elementos[0]) + _normalizar_lista_sentencias(elementos[1]))
    elif num_prod == 4:
        return elementos[0]
    elif num_prod == 5:
        return elementos[0]
    elif num_prod == 6:
        return elementos[0]
    elif num_prod == 7:
        tipo_dato = normalizar_tipo(elementos[0])
        decl_items = elementos[1] if isinstance(elementos[1], list) else [elementos[1]]
        declaraciones = [_declarar_item(tipo_dato, item) for item in decl_items]
        return Nodo('DECL_LIST', tipo_dato, declaraciones)
    elif num_prod == 8:
        return [elementos[0]]
    elif num_prod == 9:
        return elementos[0] + [elementos[2]]
    elif num_prod == 10:
        return Nodo('DECL_ITEM', elementos[0])
    elif num_prod == 11:
        return Nodo('DECL_ITEM', elementos[0], [elementos[2]])
    elif num_prod == 12:
        nombre_var = elementos[0]
        expr_nodo = elementos[2]
        valor = evaluarexpresion(expr_nodo)
        ambito, _ = buscar_variable(nombre_var)
        if ambito is None:
            raise Exception(f"Semantic error: variable '{nombre_var}' not declared")
        ambito.asignar(nombre_var, valor)
        return Nodo('ASSIGN', nombre_var, [expr_nodo])
    elif num_prod == 13:
        return Nodo('BLOCK', None, _normalizar_lista_sentencias(elementos[1]))
    elif num_prod == 14:
        return Nodo('BLOCK', None, [])
    elif num_prod == 15:
        return Nodo('+', None, [elementos[0], elementos[2]])
    elif num_prod == 16:
        return Nodo('-', None, [elementos[0], elementos[2]])
    elif num_prod == 17:
        return elementos[0]
    elif num_prod == 18:
        return Nodo('*', None, [elementos[0], elementos[2]])
    elif num_prod == 19:
        return Nodo('/', None, [elementos[0], elementos[2]])
    elif num_prod == 20:
        return elementos[0]
    elif num_prod == 21:
        return elementos[1]
    elif num_prod == 22:
        return Nodo('ID', elementos[0])
    elif num_prod == 23:
        return Nodo('CONST', parsear_constante(elementos[0]))
    return None


def imprimir_arbol(nodo, nivel=0):
    if nodo is None:
        return
    sangria = "  " * nivel
    valor = repr(nodo.valor) if isinstance(nodo.valor, str) else nodo.valor
    print(f"{sangria}{nodo.tipo}: {valor}")
    for hijo in nodo.hijos:
        imprimir_arbol(hijo, nivel + 1)


def exportar_arbol_graphviz(nodo, nombre_archivo="ast"):
    if nodo is None:
        print("No AST available.")
        return

    dot_path = f"{nombre_archivo}.dot"
    png_path = f"{nombre_archivo}.png"
    contador = [0]
    lineas = ["digraph AST {", '    node [shape=box, style="rounded"];']

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
