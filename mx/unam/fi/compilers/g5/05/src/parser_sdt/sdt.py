class Nodo:
    def __init__(self, tipo, valor=None, hijos=None, linea=None, columna=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos else []
        self.linea = linea
        self.columna = columna

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


def formatear_valor(valor):
    return repr(valor) if isinstance(valor, str) else valor


def error_semantico(mensaje, posiciones=None, indice=0, nodo=None):
    """Lanza errores semánticos con ubicación cuando está disponible."""
    if nodo is not None and getattr(nodo, "linea", None) is not None:
        raise Exception(
            f"Semantic error at line {nodo.linea}, column {nodo.columna}: {mensaje}"
        )

    if posiciones and len(posiciones) > indice:
        linea, columna = posiciones[indice]
        if linea is not None and columna is not None:
            raise Exception(f"Semantic error at line {linea}, column {columna}: {mensaje}")

    raise Exception(f"Semantic error: {mensaje}")


class TablaSimbolos:
    def __init__(self):
        self.simbolos = {}

    def limpiar(self):
        self.simbolos = {}

    def declarar(self, nombre, tipo, posiciones=None, indice=0):
        tipo = normalizar_tipo(tipo, posiciones, indice)
        if tipo == "void":
            error_semantico(f"variable '{nombre}' cannot be declared as void", posiciones, indice)
        if nombre in self.simbolos:
            error_semantico(f"variable '{nombre}' already declared", posiciones, indice)
        self.simbolos[nombre] = {'tipo': tipo, 'valor': None}

    def asignar(self, nombre, valor, posiciones=None, indice=0):
        if nombre not in self.simbolos:
            error_semantico(f"variable '{nombre}' not declared", posiciones, indice)
        tipo_destino = self.simbolos[nombre]['tipo']
        self.simbolos[nombre]['valor'] = convertir_a_tipo(
            valor, tipo_destino, nombre, posiciones, indice
        )

    def obtener(self, nombre, posiciones=None, indice=0):
        if nombre not in self.simbolos:
            error_semantico(f"variable '{nombre}' not declared", posiciones, indice)
        return self.simbolos[nombre]

    def mostrar(self):
        for nombre, datos in self.simbolos.items():
            print(f"{nombre} -> type: {datos['tipo']}, value: {formatear_valor(datos['valor'])}")

class TablaFunciones:
    def __init__(self):
        self.funciones = {}

    def limpiar(self):
        self.funciones = {}

    def declarar(self, nombre, tipo_retorno, posiciones=None, indice=0):
        tipo_retorno = normalizar_tipo(tipo_retorno, posiciones, indice)

        if nombre in self.funciones:
            error_semantico(f"function '{nombre}' already declared", posiciones, indice)

        self.funciones[nombre] = {
            'tipo_retorno': tipo_retorno,
            'parametros': []
        }

    def mostrar(self):
        for nombre, datos in self.funciones.items():
            print(
                f"{nombre} -> return type: {datos['tipo_retorno']}, "
                f"params: ()"
            )


# Contexto global para semántica
tabla_simbolos = TablaSimbolos()
tabla_funciones = TablaFunciones()
ambito_pila = [tabla_simbolos]

break_contexto = 0
loop_contexto = 0

snapshots_funcion = []
funcion_pendiente = None
funcion_contexto_pila = []

def reset_semantica():
    global ambito_pila, break_contexto, loop_contexto
    global snapshots_funcion, funcion_pendiente, funcion_contexto_pila

    tabla_simbolos.limpiar()
    tabla_funciones.limpiar()

    ambito_pila = [tabla_simbolos]

    break_contexto = 0
    loop_contexto = 0

    snapshots_funcion = []
    funcion_pendiente = None
    funcion_contexto_pila = []


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


def normalizar_tipo(tipo, posiciones=None, indice=0):
    if tipo not in VALID_TYPES:
        error_semantico(f"unknown type '{tipo}'", posiciones, indice)
    return tipo


def inferir_tipo_constante(valor, nodo=None):
    if isinstance(valor, bool):
        return "bool"
    if isinstance(valor, int):
        return "int"
    if isinstance(valor, float):
        return "double"
    if isinstance(valor, str) and len(valor) == 1:
        return "char"
    error_semantico(f"invalid constant '{valor}'", nodo=nodo)


def valor_numerico(valor):
    if isinstance(valor, bool):
        return 1 if valor else 0
    if isinstance(valor, str) and len(valor) == 1:
        return ord(valor)
    return valor


def valor_booleano(valor):
    return bool(valor_numerico(valor))


def convertir_a_tipo(valor, tipo_destino, nombre_var=None, posiciones=None, indice=0, nodo=None):
    tipo_destino = normalizar_tipo(tipo_destino, posiciones, indice)
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
                error_semantico(
                    f"cannot assign non-integer float to char{etiqueta}",
                    posiciones,
                    indice,
                    nodo,
                )
            valor = int(valor)
        if isinstance(valor, int) and 0 <= valor <= 255:
            return chr(valor)
        error_semantico(f"value '{valor}' out of char range{etiqueta}", posiciones, indice, nodo)

    if tipo_destino in ENTEROS:
        if isinstance(valor, str) and len(valor) == 1:
            valor = ord(valor)
        elif isinstance(valor, bool):
            valor = 1 if valor else 0
        elif isinstance(valor, float):
            if not valor.is_integer():
                error_semantico(
                    f"cannot assign non-integer value {valor} to {tipo_destino}{etiqueta}",
                    posiciones,
                    indice,
                    nodo,
                )
            valor = int(valor)

        if not isinstance(valor, int):
            error_semantico(f"cannot assign '{valor}' to {tipo_destino}{etiqueta}", posiciones, indice, nodo)

        minimo, maximo = RANGOS[tipo_destino]
        if not (minimo <= valor <= maximo):
            error_semantico(f"value {valor} out of range for {tipo_destino}{etiqueta}", posiciones, indice, nodo)
        return valor

    if tipo_destino in REALES:
        if isinstance(valor, str) and len(valor) == 1:
            valor = ord(valor)
        elif isinstance(valor, bool):
            valor = 1 if valor else 0
        if isinstance(valor, (int, float)):
            return float(valor)
        error_semantico(f"cannot assign '{valor}' to {tipo_destino}{etiqueta}", posiciones, indice, nodo)

    error_semantico(f"unsupported type '{tipo_destino}'", posiciones, indice, nodo)


def tipo_aritmetico(tipo_izq, tipo_der, operador):
    if tipo_izq == "double" or tipo_der == "double":
        return "double"
    if tipo_izq == "float" or tipo_der == "float":
        return "float"
    return "int"


def evaluarexpresion(nodo, con_tipo=False):
    valor, tipo = evaluar_con_tipo(nodo)
    return (valor, tipo) if con_tipo else valor


def evaluar_con_tipo(nodo):
    if nodo is None:
        error_semantico("invalid expression")

    if nodo.tipo == 'CONST':
        return nodo.valor, inferir_tipo_constante(nodo.valor, nodo)

    if nodo.tipo == 'ID':
        ambito, var_info = buscar_variable(nodo.valor)
        if ambito is None:
            error_semantico(f"variable '{nodo.valor}' not declared", nodo=nodo)
        if var_info['valor'] is None:
            error_semantico(f"variable '{nodo.valor}' used before initialization", nodo=nodo)
        return var_info['valor'], var_info['tipo']

    if nodo.tipo == '!':
        valor, _ = evaluar_con_tipo(nodo.hijos[0])
        return not valor_booleano(valor), "bool"

    if nodo.tipo == '&&':
        izq, _ = evaluar_con_tipo(nodo.hijos[0])
        der, _ = evaluar_con_tipo(nodo.hijos[1])
        return valor_booleano(izq) and valor_booleano(der), "bool"

    if nodo.tipo == '||':
        izq, _ = evaluar_con_tipo(nodo.hijos[0])
        der, _ = evaluar_con_tipo(nodo.hijos[1])
        return valor_booleano(izq) or valor_booleano(der), "bool"

    if nodo.tipo in {'==', '!=', '<', '>', '<=', '>='}:
        izq, _ = evaluar_con_tipo(nodo.hijos[0])
        der, _ = evaluar_con_tipo(nodo.hijos[1])

        izq_val = valor_numerico(izq)
        der_val = valor_numerico(der)

        if nodo.tipo == '==':
            return izq_val == der_val, "bool"
        if nodo.tipo == '!=':
            return izq_val != der_val, "bool"
        if nodo.tipo == '<':
            return izq_val < der_val, "bool"
        if nodo.tipo == '>':
            return izq_val > der_val, "bool"
        if nodo.tipo == '<=':
            return izq_val <= der_val, "bool"
        if nodo.tipo == '>=':
            return izq_val >= der_val, "bool"

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
                error_semantico("division by zero", nodo=nodo)

            if tipo_res == "int":
                valor = int(izq_num / der_num)
            else:
                valor = izq_num / der_num

        if tipo_res == "int":
            valor = int(valor)
        else:
            valor = float(valor)

        return valor, tipo_res

    error_semantico(f"unknown operator '{nodo.tipo}'", nodo=nodo)


def _declarar_item(tipo_dato, item):
    nombre_var = item.valor
    expr_nodo = item.hijos[0] if item.hijos else None
    tabla_actual = obtener_tabla_actual()
    pos_item = [(item.linea, item.columna)] if item.linea is not None else None

    tabla_actual.declarar(nombre_var, tipo_dato, pos_item, 0)

    if expr_nodo is not None:
        valor = evaluarexpresion(expr_nodo)
        tabla_actual.asignar(nombre_var, valor, pos_item, 0)

    hijos = [Nodo('TYPE', tipo_dato, linea=item.linea, columna=item.columna)]
    if expr_nodo is not None:
        hijos.append(expr_nodo)

    return Nodo('DECL', nombre_var, hijos, linea=item.linea, columna=item.columna)


def _normalizar_lista_sentencias(nodo):
    if nodo is None:
        return []
    if isinstance(nodo, Nodo) and nodo.tipo == 'STMT_LIST':
        return nodo.hijos
    return [nodo]


def parsear_constante(val, posiciones=None, indice=0):
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
                error_semantico(f"invalid char literal {val}", posiciones, indice)
            return contenido
        try:
            return float(val) if '.' in val else int(val)
        except ValueError:
            error_semantico(f"invalid constant '{val}'", posiciones, indice)
    error_semantico(f"invalid constant '{val}'", posiciones, indice)


def _pos(posiciones, indice):
    if posiciones and len(posiciones) > indice:
        return posiciones[indice]
    return (None, None)


def _nodo_binario(operador, elementos, posiciones=None):
    linea, columna = _pos(posiciones, 1)
    return Nodo(
        operador,
        None,
        [elementos[0], elementos[2]],
        linea=linea,
        columna=columna
    )


def _nodo_unario(operador, elementos, posiciones=None):
    linea, columna = _pos(posiciones, 0)
    return Nodo(
        operador,
        None,
        [elementos[1]],
        linea=linea,
        columna=columna
    )


def _validar_condicion(condicion):
    """
    Valida semánticamente la condición del if.

    No ejecuta el if.
    Solo evalúa la expresión para detectar errores como:
    - variable no declarada
    - variable sin inicializar
    - división entre cero
    - operadores inválidos
    """
    valor, tipo = evaluarexpresion(condicion, con_tipo=True)

    if tipo == "void":
        error_semantico("if condition cannot be void", nodo=condicion)

    return valor, tipo


def _crear_asignacion(nombre_var, expr_nodo, posiciones=None, aplicar=True):
    valor = evaluarexpresion(expr_nodo)

    ambito, var_info = buscar_variable(nombre_var)
    if ambito is None:
        error_semantico(f"variable '{nombre_var}' not declared", posiciones, 0)

    if aplicar:
        ambito.asignar(nombre_var, valor, posiciones, 0)
    else:
        # Solo valida compatibilidad de tipo, sin modificar la tabla.
        convertir_a_tipo(valor, var_info['tipo'], nombre_var, posiciones, 0)

    linea, columna = _pos(posiciones, 0)
    return Nodo(
        'ASSIGN',
        nombre_var,
        [expr_nodo],
        linea=linea,
        columna=columna
    )


def _crear_incdec(nombre_var, operador, posiciones=None, aplicar=False):
    ambito, var_info = buscar_variable(nombre_var)

    if ambito is None:
        error_semantico(f"variable '{nombre_var}' not declared", posiciones, 0)

    if var_info['valor'] is None:
        error_semantico(f"variable '{nombre_var}' used before initialization", posiciones, 0)

    tipo_var = var_info['tipo']

    if tipo_var not in ENTEROS | REALES | {"char"}:
        error_semantico(
            f"operator '{operador}' cannot be applied to type '{tipo_var}'",
            posiciones,
            0
        )

    valor_actual = valor_numerico(var_info['valor'])

    if operador == "++":
        nuevo_valor = valor_actual + 1
    else:
        nuevo_valor = valor_actual - 1

    if aplicar:
        ambito.asignar(nombre_var, nuevo_valor, posiciones, 0)
    else:
        convertir_a_tipo(nuevo_valor, tipo_var, nombre_var, posiciones, 0)

    linea, columna = _pos(posiciones, 0)
    return Nodo(
        operador,
        nombre_var,
        [],
        linea=linea,
        columna=columna
    )


def _validar_switch(expr_switch, cases, default_item=None, posiciones=None):
    valor_switch, tipo_switch = evaluarexpresion(expr_switch, con_tipo=True)

    valores_vistos = set()

    for case in cases:
        const_nodo = case.hijos[0]
        valor_case, tipo_case = evaluarexpresion(const_nodo, con_tipo=True)

        try:
            valor_convertido = convertir_a_tipo(
                valor_case,
                tipo_switch,
                None,
                posiciones,
                0,
                nodo=const_nodo
            )
        except Exception:
            error_semantico(
                f"case value type '{tipo_case}' is not compatible with switch type '{tipo_switch}'",
                nodo=const_nodo
            )

        if valor_convertido in valores_vistos:
            error_semantico(
                f"duplicate case value '{valor_convertido}'",
                nodo=const_nodo
            )

        valores_vistos.add(valor_convertido)


def entrar_break_contexto():
    global break_contexto
    break_contexto += 1


def salir_break_contexto():
    global break_contexto
    if break_contexto > 0:
        break_contexto -= 1


def validar_break(posiciones=None):
    if break_contexto <= 0:
        error_semantico("'break' statement not within loop or switch", posiciones, 0)


def entrar_loop_contexto():
    global loop_contexto
    loop_contexto += 1


def salir_loop_contexto():
    global loop_contexto
    if loop_contexto > 0:
        loop_contexto -= 1


def validar_continue(posiciones=None):
    if loop_contexto <= 0:
        error_semantico("'continue' statement not within loop", posiciones, 0)


def _snapshot_ambitos():
    return [
        {nombre: datos.copy() for nombre, datos in ambito.simbolos.items()}
        for ambito in ambito_pila
    ]


def entrar_funcion_contexto():
    global funcion_pendiente

    snapshots_funcion.append(_snapshot_ambitos())

    if funcion_pendiente is not None:
        funcion_contexto_pila.append(funcion_pendiente)
        funcion_pendiente = None
    else:
        funcion_contexto_pila.append(None)


def salir_funcion_contexto():
    if funcion_contexto_pila:
        funcion_contexto_pila.pop()

    if not snapshots_funcion:
        return

    snapshot = snapshots_funcion.pop()

    for ambito, simbolos_guardados in zip(ambito_pila, snapshot):
        ambito.simbolos = {
            nombre: datos.copy()
            for nombre, datos in simbolos_guardados.items()
        }


def obtener_funcion_actual():
    if not funcion_contexto_pila:
        return None
    return funcion_contexto_pila[-1]


def validar_return(expr_nodo=None, posiciones=None):
    funcion_actual = obtener_funcion_actual()

    if funcion_actual is None:
        error_semantico("'return' statement not within function", posiciones, 0)

    tipo_retorno = funcion_actual['tipo_retorno']
    funcion_actual['tiene_return'] = True

    if expr_nodo is None:
        if tipo_retorno != "void":
            error_semantico(
                f"function '{funcion_actual['nombre']}' must return a value of type '{tipo_retorno}'",
                posiciones,
                0
            )

        return None

    if tipo_retorno == "void":
        error_semantico(
            f"void function '{funcion_actual['nombre']}' should not return a value",
            posiciones,
            0
        )

    valor, _ = evaluarexpresion(expr_nodo, con_tipo=True)

    convertir_a_tipo(
        valor,
        tipo_retorno,
        f"return of function '{funcion_actual['nombre']}'",
        posiciones,
        0,
        nodo=expr_nodo
    )

    return expr_nodo


def accion_semantica(produccion, elementos, posiciones=None):
    lhs, rhs = produccion
    rhs = tuple(rhs)

    # Programa
    if lhs == "Program'" and rhs == ("Program",):
        return elementos[0]

    elif lhs == "Program" and rhs == ("TopLevelList",):
        return Nodo('PROGRAM', None, elementos[0])

    # Lista de statements
    elif lhs == "StatementList" and rhs == ("Statement",):
        return Nodo('STMT_LIST', None, _normalizar_lista_sentencias(elementos[0]))

    elif lhs == "StatementList" and rhs == ("StatementList", "Statement"):
        return Nodo(
            'STMT_LIST',
            None,
            _normalizar_lista_sentencias(elementos[0]) +
            _normalizar_lista_sentencias(elementos[1])
        )
    
    elif lhs == "TopLevelList" and rhs == ("TopLevel",):
        return [elementos[0]]

    elif lhs == "TopLevelList" and rhs == ("TopLevelList", "TopLevel"):
        return elementos[0] + [elementos[1]]

    elif lhs == "TopLevel" and rhs == ("Statement",):
        return elementos[0]

    elif lhs == "TopLevel" and rhs == ("FunctionDecl",):
        return elementos[0]

    # Statements
    elif lhs == "Statement" and rhs == ("Declaration", ";"):
        return elementos[0]

    elif lhs == "Statement" and rhs == ("Assignment", ";"):
        return elementos[0]

    elif lhs == "Statement" and rhs == ("Block",):
        return elementos[0]

    elif lhs == "Statement" and rhs == ("IfStatement",):
        return elementos[0]

    elif lhs == "Statement" and rhs == ("WhileStatement",):
        return elementos[0]

    # Declaración
    elif lhs == "Declaration" and rhs == ("TYPE", "DeclList"):
        tipo_dato = normalizar_tipo(elementos[0], posiciones, 0)
        decl_items = elementos[1] if isinstance(elementos[1], list) else [elementos[1]]
        declaraciones = [_declarar_item(tipo_dato, item) for item in decl_items]
        linea, columna = _pos(posiciones, 0)
        return Nodo('DECL_LIST', tipo_dato, declaraciones, linea=linea, columna=columna)

    elif lhs == "DeclList" and rhs == ("DeclItem",):
        return [elementos[0]]

    elif lhs == "DeclList" and rhs == ("DeclList", ",", "DeclItem"):
        return elementos[0] + [elementos[2]]

    elif lhs == "DeclItem" and rhs == ("ID",):
        linea, columna = _pos(posiciones, 0)
        return Nodo('DECL_ITEM', elementos[0], linea=linea, columna=columna)

    elif lhs == "DeclItem" and rhs == ("ID", "=", "E"):
        linea, columna = _pos(posiciones, 0)
        return Nodo('DECL_ITEM', elementos[0], [elementos[2]], linea=linea, columna=columna)

    # Asignación
    elif lhs == "Assignment" and rhs == ("ID", "=", "E"):
        return _crear_asignacion(
            elementos[0],
            elementos[2],
            posiciones,
            aplicar=True
        )

    # Bloques
    elif lhs == "Block" and rhs == ("{", "StatementList", "}"):
        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'BLOCK',
            None,
            _normalizar_lista_sentencias(elementos[1]),
            linea=linea,
            columna=columna
        )

    elif lhs == "Block" and rhs == ("{", "}"):
        linea, columna = _pos(posiciones, 0)
        return Nodo('BLOCK', None, [], linea=linea, columna=columna)

    # If / else
    elif lhs == "IfStatement" and rhs == ("if", "(", "E", ")", "Block"):
        condicion = elementos[2]
        bloque_then = elementos[4]

        _validar_condicion(condicion)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'IF',
            None,
            [condicion, bloque_then],
            linea=linea,
            columna=columna
        )

    elif lhs == "IfStatement" and rhs == ("if", "(", "E", ")", "Block", "else", "Block"):
        condicion = elementos[2]
        bloque_then = elementos[4]
        bloque_else = elementos[6]

        _validar_condicion(condicion)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'IF_ELSE',
            None,
            [condicion, bloque_then, bloque_else],
            linea=linea,
            columna=columna
        )

    # While
    elif lhs == "WhileStatement" and rhs == (
        "while", "(", "E", ")", "EnterBreak", "EnterLoop", "Block", "ExitLoop", "ExitBreak"
    ):
        condicion = elementos[2]
        bloque = elementos[6]

        _validar_condicion(condicion)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'WHILE',
            None,
            [condicion, bloque],
            linea=linea,
            columna=columna
        )
    
    # For
    elif lhs == "Statement" and rhs == ("ForStatement",):
        return elementos[0]

    elif lhs == "ForStatement" and rhs == (
        "for", "(", "ForInit", ";", "E", ";", "ForUpdate", ")", "EnterBreak", "EnterLoop", "Block", "ExitLoop", "ExitBreak"
    ):
        inicializacion = elementos[2]
        condicion = elementos[4]
        actualizacion = elementos[6]
        bloque = elementos[10]

        _validar_condicion(condicion)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'FOR',
            None,
            [inicializacion, condicion, actualizacion, bloque],
            linea=linea,
            columna=columna
        )

    elif lhs == "ForInit" and rhs == ("ID", "=", "E"):
        return _crear_asignacion(
            elementos[0],
            elementos[2],
            posiciones,
            aplicar=True
        )

    elif lhs == "ForInit" and rhs == ("Declaration",):
        return elementos[0]

    elif lhs == "ForUpdate" and rhs == ("ID", "=", "E"):
        return _crear_asignacion(
            elementos[0],
            elementos[2],
            posiciones,
            aplicar=False
        )
    
    elif lhs == "ForUpdate" and rhs == ("ID", "++"):
        return _crear_incdec(
            elementos[0],
            "++",
            posiciones,
            aplicar=False
        )

    elif lhs == "ForUpdate" and rhs == ("ID", "--"):
        return _crear_incdec(
            elementos[0],
            "--",
            posiciones,
            aplicar=False
    )

    # Switch
    elif lhs == "Statement" and rhs == ("SwitchStatement",):
        return elementos[0]

    elif lhs == "SwitchStatement" and rhs == (
        "switch", "(", "E", ")", "{", "EnterBreak", "CaseList", "}", "ExitBreak"
    ):
        expr_switch = elementos[2]
        cases = elementos[6]
        _validar_switch(expr_switch, cases, None, posiciones)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'SWITCH',
            None,
            [expr_switch] + cases,
            linea=linea,
            columna=columna
        )

    elif lhs == "SwitchStatement" and rhs == (
        "switch", "(", "E", ")", "{", "EnterBreak", "CaseList", "DefaultItem", "}", "ExitBreak"
    ):
        expr_switch = elementos[2]
        cases = elementos[6]
        default_item = elementos[7]

        _validar_switch(expr_switch, cases, default_item, posiciones)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'SWITCH',
            None,
            [expr_switch] + cases + [default_item],
            linea=linea,
            columna=columna
        )

    elif lhs == "SwitchStatement" and rhs == (
        "switch", "(", "E", ")", "{", "EnterBreak", "DefaultItem", "}", "ExitBreak"
    ):
        expr_switch = elementos[2]
        default_item = elementos[6]

        evaluarexpresion(expr_switch, con_tipo=True)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'SWITCH',
            None,
            [expr_switch, default_item],
            linea=linea,
            columna=columna
        )

    elif lhs == "CaseList" and rhs == ("CaseItem",):
        return [elementos[0]]

    elif lhs == "CaseList" and rhs == ("CaseList", "CaseItem"):
        return elementos[0] + [elementos[1]]

    elif lhs == "CaseItem" and rhs == ("case", "CONST", ":", "Block"):
        linea, columna = _pos(posiciones, 0)
        const_linea, const_columna = _pos(posiciones, 1)

        return Nodo(
            'CASE',
            None,
            [
                Nodo(
                    'CONST',
                    parsear_constante(elementos[1], posiciones, 1),
                    linea=const_linea,
                    columna=const_columna
                ),
                elementos[3]
            ],
            linea=linea,
            columna=columna
        )

    elif lhs == "DefaultItem" and rhs == ("default", ":", "Block"):
        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'DEFAULT',
            None,
            [elementos[2]],
            linea=linea,
            columna=columna
        )

    # Marcadores de break
    elif lhs == "EnterBreak" and rhs == tuple():
        entrar_break_contexto()
        return None

    elif lhs == "ExitBreak" and rhs == tuple():
        salir_break_contexto()
        return None

    # Break
    elif lhs == "Statement" and rhs == ("BreakStatement", ";"):
        return elementos[0]

    elif lhs == "BreakStatement" and rhs == ("break",):
        validar_break(posiciones)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'BREAK',
            None,
            [],
            linea=linea,
            columna=columna
        )
    
    #Marcadores de loop
    elif lhs == "EnterLoop" and rhs == tuple():
        entrar_loop_contexto()
        return None

    elif lhs == "ExitLoop" and rhs == tuple():
        salir_loop_contexto()
        return None
    
    # Continue
    elif lhs == "Statement" and rhs == ("ContinueStatement", ";"):
        return elementos[0]

    elif lhs == "ContinueStatement" and rhs == ("continue",):
        validar_continue(posiciones)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'CONTINUE',
            None,
            [],
            linea=linea,
            columna=columna
        )

    # Expresiones de paso directo
    elif lhs == "E" and rhs == ("OrExpr",):
        return elementos[0]

    elif lhs == "OrExpr" and rhs == ("AndExpr",):
        return elementos[0]

    elif lhs == "AndExpr" and rhs == ("EqExpr",):
        return elementos[0]

    elif lhs == "EqExpr" and rhs == ("RelExpr",):
        return elementos[0]

    elif lhs == "RelExpr" and rhs == ("AddExpr",):
        return elementos[0]

    elif lhs == "AddExpr" and rhs == ("MulExpr",):
        return elementos[0]

    elif lhs == "MulExpr" and rhs == ("UnaryExpr",):
        return elementos[0]

    elif lhs == "UnaryExpr" and rhs == ("Primary",):
        return elementos[0]

    # Operadores binarios
    elif len(rhs) == 3 and rhs[1] in {
        '||', '&&',
        '==', '!=',
        '<', '>', '<=', '>=',
        '+', '-', '*', '/'
    }:
        return _nodo_binario(rhs[1], elementos, posiciones)

    # Operador unario
    elif lhs == "UnaryExpr" and rhs == ("!", "UnaryExpr"):
        return _nodo_unario('!', elementos, posiciones)

    # Primary
    elif lhs == "Primary" and rhs == ("(", "E", ")"):
        return elementos[1]

    elif lhs == "Primary" and rhs == ("ID",):
        linea, columna = _pos(posiciones, 0)
        return Nodo('ID', elementos[0], linea=linea, columna=columna)

    elif lhs == "Primary" and rhs == ("CONST",):
        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'CONST',
            parsear_constante(elementos[0], posiciones, 0),
            linea=linea,
            columna=columna
        )
    
    # Funciones
    elif lhs == "FunctionHeader" and rhs == ("TYPE", "ID", "(", ")"):
        global funcion_pendiente

        tipo_retorno = normalizar_tipo(elementos[0], posiciones, 0)
        nombre_funcion = elementos[1]

        tabla_funciones.declarar(nombre_funcion, tipo_retorno, posiciones, 1)

        linea, columna = _pos(posiciones, 1)

        header = {
            'nombre': nombre_funcion,
            'tipo_retorno': tipo_retorno,
            'linea': linea,
            'columna': columna,
            'tiene_return': False
        }

        funcion_pendiente = header

        return header

    elif lhs == "EnterFunction" and rhs == tuple():
        entrar_funcion_contexto()
        return None

    elif lhs == "ExitFunction" and rhs == tuple():
        salir_funcion_contexto()
        return None

    elif lhs == "FunctionDecl" and rhs == (
        "FunctionHeader", "EnterFunction", "Block", "ExitFunction"
    ):
        header = elementos[0]
        bloque = elementos[2]

        if header is None:
            return None

        return Nodo(
            'FUNCTION',
            header['nombre'],
            [
                Nodo('RETURN_TYPE', header['tipo_retorno']),
                bloque
            ],
            linea=header['linea'],
            columna=header['columna']
        )
    
    # Return
    elif lhs == "Statement" and rhs == ("ReturnStatement", ";"):
        return elementos[0]

    elif lhs == "ReturnStatement" and rhs == ("return",):
        validar_return(None, posiciones)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'RETURN',
            None,
            [],
            linea=linea,
            columna=columna
        )

    elif lhs == "ReturnStatement" and rhs == ("return", "E"):
        expr_nodo = elementos[1]

        validar_return(expr_nodo, posiciones)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'RETURN',
            None,
            [expr_nodo],
            linea=linea,
            columna=columna
        )

    error_semantico(
        f"semantic action not implemented for production: {lhs} -> {' '.join(rhs)}",
        posiciones,
        0
    )


def imprimir_arbol(nodo, nivel=0):
    if nodo is None:
        return
    sangria = "  " * nivel
    print(f"{sangria}{nodo.tipo}: {formatear_valor(nodo.valor)}")
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

    def escapar_dot(texto):
        return str(texto).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    def recorrer(n):
        node_id = f"n{contador[0]}"
        contador[0] += 1
        etiqueta = n.tipo
        if n.valor is not None:
            etiqueta += f"\\n{escapar_dot(formatear_valor(n.valor))}"
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
