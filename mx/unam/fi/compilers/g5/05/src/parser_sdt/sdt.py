class Nodo:
    def __init__(self, tipo, valor=None, hijos=None, linea=None, columna=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos else []
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"Nodo({self.tipo}, {self.valor}, {self.hijos})"


class ValorString:
    def __init__(self, valor):
        self.valor = valor

    def __repr__(self):
        return repr(self.valor)


def es_string_literal(valor):
    return isinstance(valor, ValorString)


class ValorDesconocido:
    def __init__(self, tipo, descripcion=None):
        self.tipo = tipo
        self.descripcion = descripcion

    def __repr__(self):
        if self.descripcion:
            return f"<unknown:{self.tipo}:{self.descripcion}>"
        return f"<unknown:{self.tipo}>"


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
    if es_valor_desconocido(valor):
        return repr(valor)

    if es_string_literal(valor):
        return repr(valor.valor)

    return repr(valor) if isinstance(valor, str) else valor


def es_valor_desconocido(valor):
    return isinstance(valor, ValorDesconocido)


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
            if datos.get('es_array', False):
                if datos.get('dimensiones') == 2:
                    valores = [
                        [formatear_valor(v) for v in fila]
                        for fila in datos['valor']
                    ]
                    print(
                        f"{nombre} -> type: {datos['tipo']}[{datos['filas']}][{datos['columnas']}], "
                        f"value: {valores}"
                    )
                else:
                    valores = [formatear_valor(v) for v in datos['valor']]
                    print(
                        f"{nombre} -> type: {datos['tipo']}[{datos['tamano']}], "
                        f"value: {valores}"
                    )
            else:
                print(
                    f"{nombre} -> type: {datos['tipo']}, "
                    f"value: {formatear_valor(datos['valor'])}"
                )

    def declarar_array(self, nombre, tipo, tamano, posiciones=None, indice=0):
        tipo = normalizar_tipo(tipo, posiciones, indice)

        if tipo == "void":
            error_semantico(f"array '{nombre}' cannot be declared as void", posiciones, indice)

        if nombre in self.simbolos:
            error_semantico(f"variable '{nombre}' already declared", posiciones, indice)

        if not isinstance(tamano, int):
            error_semantico(f"array size for '{nombre}' must be an integer", posiciones, indice)

        if tamano <= 0:
            error_semantico(f"array size for '{nombre}' must be greater than zero", posiciones, indice)

        self.simbolos[nombre] = {
            'tipo': tipo,
            'valor': [None] * tamano,
            'es_array': True,
            'tamano': tamano
        }

    def declarar_matriz(self, nombre, tipo, filas, columnas, posiciones=None, indice=0):
        tipo = normalizar_tipo(tipo, posiciones, indice)

        if tipo == "void":
            error_semantico(f"matrix '{nombre}' cannot be declared as void", posiciones, indice)

        if nombre in self.simbolos:
            error_semantico(f"variable '{nombre}' already declared", posiciones, indice)

        if not isinstance(filas, int) or not isinstance(columnas, int):
            error_semantico(f"matrix dimensions for '{nombre}' must be integers", posiciones, indice)

        if filas <= 0 or columnas <= 0:
            error_semantico(
                f"matrix dimensions for '{nombre}' must be greater than zero",
                posiciones,
                indice
            )

        self.simbolos[nombre] = {
            'tipo': tipo,
            'valor': [[None for _ in range(columnas)] for _ in range(filas)],
            'es_array': True,
            'dimensiones': 2,
            'filas': filas,
            'columnas': columnas
        }

    def asignar_array(self, nombre, indice_array, valor, posiciones=None, indice=0, nodo=None):
        if nombre not in self.simbolos:
            error_semantico(f"array '{nombre}' not declared", posiciones, indice, nodo)

        datos = self.simbolos[nombre]

        if not datos.get('es_array', False):
            error_semantico(f"variable '{nombre}' is not an array", posiciones, indice, nodo)

        if datos.get('dimensiones', 1) != 1:
            error_semantico(f"variable '{nombre}' is not a one-dimensional array", posiciones, indice, nodo)

        if es_valor_desconocido(indice_array):
            error_semantico(
                f"array index for '{nombre}' must be known at semantic analysis",
                posiciones,
                indice,
                nodo
            )

        if not isinstance(indice_array, int):
            error_semantico(f"array index for '{nombre}' must be an integer", posiciones, indice, nodo)

        if indice_array < 0 or indice_array >= datos['tamano']:
            error_semantico(
                f"array index {indice_array} out of bounds for '{nombre}' with size {datos['tamano']}",
                posiciones,
                indice,
                nodo
            )

        datos['valor'][indice_array] = convertir_a_tipo(
            valor,
            datos['tipo'],
            f"{nombre}[{indice_array}]",
            posiciones,
            indice,
            nodo
        )
    
    def asignar_matriz(self, nombre, fila, columna, valor, posiciones=None, indice=0, nodo=None):
        if nombre not in self.simbolos:
            error_semantico(f"matrix '{nombre}' not declared", posiciones, indice, nodo)

        datos = self.simbolos[nombre]

        if not datos.get('es_array', False) or datos.get('dimensiones') != 2:
            error_semantico(f"variable '{nombre}' is not a matrix", posiciones, indice, nodo)

        if es_valor_desconocido(fila) or es_valor_desconocido(columna):
            error_semantico(
                f"matrix indices for '{nombre}' must be known at semantic analysis",
                posiciones,
                indice,
                nodo
            )

        if not isinstance(fila, int) or not isinstance(columna, int):
            error_semantico(f"matrix indices for '{nombre}' must be integers", posiciones, indice, nodo)

        if fila < 0 or fila >= datos['filas']:
            error_semantico(
                f"matrix row index {fila} out of bounds for '{nombre}' with {datos['filas']} row(s)",
                posiciones,
                indice,
                nodo
            )

        if columna < 0 or columna >= datos['columnas']:
            error_semantico(
                f"matrix column index {columna} out of bounds for '{nombre}' with {datos['columnas']} column(s)",
                posiciones,
                indice,
                nodo
            )

        datos['valor'][fila][columna] = convertir_a_tipo(
            valor,
            datos['tipo'],
            f"{nombre}[{fila}][{columna}]",
            posiciones,
            indice,
            nodo
        )

    def obtener_array(self, nombre, indice_array, posiciones=None, indice=0, nodo=None):
        if nombre not in self.simbolos:
            error_semantico(f"array '{nombre}' not declared", posiciones, indice, nodo)

        datos = self.simbolos[nombre]

        if not datos.get('es_array', False):
            error_semantico(f"variable '{nombre}' is not an array", posiciones, indice, nodo)

        if datos.get('dimensiones', 1) != 1:
            error_semantico(f"variable '{nombre}' is not a one-dimensional array", posiciones, indice, nodo)

        if es_valor_desconocido(indice_array):
            return ValorDesconocido(datos['tipo'], f"{nombre}[unknown]"), datos['tipo']

        if not isinstance(indice_array, int):
            error_semantico(f"array index for '{nombre}' must be an integer", posiciones, indice, nodo)

        if indice_array < 0 or indice_array >= datos['tamano']:
            error_semantico(
                f"array index {indice_array} out of bounds for '{nombre}' with size {datos['tamano']}",
                posiciones,
                indice,
                nodo
            )

        valor = datos['valor'][indice_array]

        if valor is None:
            error_semantico(
                f"array element '{nombre}[{indice_array}]' used before initialization",
                posiciones,
                indice,
                nodo
            )

        return valor, datos['tipo']
    
    def obtener_matriz(self, nombre, fila, columna, posiciones=None, indice=0, nodo=None):
        if nombre not in self.simbolos:
            error_semantico(f"matrix '{nombre}' not declared", posiciones, indice, nodo)

        datos = self.simbolos[nombre]

        if not datos.get('es_array', False) or datos.get('dimensiones') != 2:
            error_semantico(f"variable '{nombre}' is not a matrix", posiciones, indice, nodo)

        if es_valor_desconocido(fila) or es_valor_desconocido(columna):
            return ValorDesconocido(datos['tipo'], f"{nombre}[unknown][unknown]"), datos['tipo']

        if not isinstance(fila, int) or not isinstance(columna, int):
            error_semantico(f"matrix indices for '{nombre}' must be integers", posiciones, indice, nodo)

        if fila < 0 or fila >= datos['filas']:
            error_semantico(
                f"matrix row index {fila} out of bounds for '{nombre}' with {datos['filas']} row(s)",
                posiciones,
                indice,
                nodo
            )

        if columna < 0 or columna >= datos['columnas']:
            error_semantico(
                f"matrix column index {columna} out of bounds for '{nombre}' with {datos['columnas']} column(s)",
                posiciones,
                indice,
                nodo
            )

        valor = datos['valor'][fila][columna]

        if valor is None:
            error_semantico(
                f"matrix element '{nombre}[{fila}][{columna}]' used before initialization",
                posiciones,
                indice,
                nodo
            )

        return valor, datos['tipo']
    
class TablaFunciones:
    def __init__(self):
        self.funciones = {}

    def limpiar(self):
        self.funciones = {}

    def declarar(self, nombre, tipo_retorno, parametros=None, posiciones=None, indice=0):
        tipo_retorno = normalizar_tipo(tipo_retorno, posiciones, indice)

        if parametros is None:
            parametros = []

        if nombre in self.funciones:
            error_semantico(f"function '{nombre}' already declared", posiciones, indice)

        nombres_param = set()

        for param in parametros:
            tipo_param = normalizar_tipo(param['tipo'], posiciones, indice)

            if tipo_param == "void":
                error_semantico(
                    f"parameter '{param['nombre']}' cannot be void",
                    posiciones,
                    indice
                )

            if param['nombre'] in nombres_param:
                error_semantico(
                    f"duplicate parameter '{param['nombre']}' in function '{nombre}'",
                    posiciones,
                    indice
                )

            nombres_param.add(param['nombre'])

        self.funciones[nombre] = {
            'tipo_retorno': tipo_retorno,
            'parametros': parametros
        }

    def obtener(self, nombre, posiciones=None, indice=0):
        if nombre not in self.funciones:
            error_semantico(f"function '{nombre}' not declared", posiciones, indice)

        return self.funciones[nombre]

    def mostrar(self):
        for nombre, datos in self.funciones.items():
            params = ", ".join(
                f"{p['tipo']} {p['nombre']}"
                for p in datos['parametros']
            )

            print(
                f"{nombre} -> return type: {datos['tipo_retorno']}, "
                f"params: ({params})"
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
    if es_string_literal(valor):
        return "string"

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
    if es_valor_desconocido(valor):
        return valor
    if isinstance(valor, bool):
        return 1 if valor else 0
    if isinstance(valor, str) and len(valor) == 1:
        return ord(valor)
    return valor


def valor_booleano(valor):
    return bool(valor_numerico(valor))


def tipos_convertibles(tipo_origen, tipo_destino):
    tipo_origen = normalizar_tipo(tipo_origen)
    tipo_destino = normalizar_tipo(tipo_destino)

    if tipo_destino == "void" or tipo_origen == "void":
        return tipo_origen == tipo_destino

    if tipo_origen == tipo_destino:
        return True

    if tipo_destino == "bool":
        return tipo_origen in ENTEROS | REALES | {"char", "bool"}

    if tipo_destino == "char":
        return tipo_origen in ENTEROS | {"char", "bool"}

    if tipo_destino in ENTEROS:
        return tipo_origen in ENTEROS | {"char", "bool"}

    if tipo_destino in REALES:
        return tipo_origen in ENTEROS | REALES | {"char", "bool"}

    return False


def convertir_a_tipo(valor, tipo_destino, nombre_var=None, posiciones=None, indice=0, nodo=None):
    tipo_destino = normalizar_tipo(tipo_destino, posiciones, indice)
    etiqueta = f" for variable '{nombre_var}'" if nombre_var else ""

    if es_valor_desconocido(valor):
        if not tipos_convertibles(valor.tipo, tipo_destino):
            error_semantico(
                f"cannot convert value of type '{valor.tipo}' to '{tipo_destino}'{etiqueta}",
                posiciones,
                indice,
                nodo,
            )

        return ValorDesconocido(tipo_destino, valor.descripcion)

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

        if var_info.get('es_array', False):
            error_semantico(
                f"array '{nodo.valor}' cannot be used as a scalar expression",
                nodo=nodo
            )

        if var_info['valor'] is None:
            error_semantico(f"variable '{nodo.valor}' used before initialization", nodo=nodo)

        return var_info['valor'], var_info['tipo']
    
    if nodo.tipo == 'ARRAY_ACCESS':
        return _evaluar_array_access(nodo)
    
    if nodo.tipo == 'MATRIX_ACCESS':
        return _evaluar_matrix_access(nodo)

    if nodo.tipo == 'CALL':
        info_funcion = tabla_funciones.obtener(nodo.valor)

        tipo_retorno = info_funcion['tipo_retorno']

        if tipo_retorno == "void":
            error_semantico(
                f"void function '{nodo.valor}' cannot be used as an expression",
                nodo=nodo
            )

        return ValorDesconocido(tipo_retorno, f"call {nodo.valor}"), tipo_retorno

    if nodo.tipo == '!':
        valor, _ = evaluar_con_tipo(nodo.hijos[0])

        if es_valor_desconocido(valor):
            return ValorDesconocido("bool", f"!{valor.descripcion}"), "bool"

        return not valor_booleano(valor), "bool"
    
    if nodo.tipo == 'NEG':
        valor, tipo = evaluar_con_tipo(nodo.hijos[0])

        if tipo not in ENTEROS | REALES | {"char", "bool"}:
            error_semantico(
                f"unary '-' cannot be applied to type '{tipo}'",
                nodo=nodo
            )

        if es_valor_desconocido(valor):
            return ValorDesconocido(tipo, "unary -"), tipo

        valor_num = valor_numerico(valor)
        resultado = -valor_num

        if tipo in ENTEROS:
            return int(resultado), "int"

        if tipo in REALES:
            return float(resultado), tipo

        if tipo == "char" or tipo == "bool":
            return int(resultado), "int"
        
    if nodo.tipo == 'POS':
        valor, tipo = evaluar_con_tipo(nodo.hijos[0])

        if tipo not in ENTEROS | REALES | {"char", "bool"}:
            error_semantico(
                f"unary '+' cannot be applied to type '{tipo}'",
                nodo=nodo
            )

        if es_valor_desconocido(valor):
            return ValorDesconocido(tipo, "unary +"), tipo

        valor_num = valor_numerico(valor)

        if tipo in ENTEROS:
            return int(valor_num), "int"

        if tipo in REALES:
            return float(valor_num), tipo

        if tipo == "char" or tipo == "bool":
            return int(valor_num), "int"

    if nodo.tipo == '&&':
        izq, _ = evaluar_con_tipo(nodo.hijos[0])
        der, _ = evaluar_con_tipo(nodo.hijos[1])

        if es_valor_desconocido(izq) or es_valor_desconocido(der):
            return ValorDesconocido("bool", "logical &&"), "bool"

        return valor_booleano(izq) and valor_booleano(der), "bool"

    if nodo.tipo == '||':
        izq, _ = evaluar_con_tipo(nodo.hijos[0])
        der, _ = evaluar_con_tipo(nodo.hijos[1])

        if es_valor_desconocido(izq) or es_valor_desconocido(der):
            return ValorDesconocido("bool", "logical ||"), "bool"

        return valor_booleano(izq) or valor_booleano(der), "bool"

    if nodo.tipo in {'==', '!=', '<', '>', '<=', '>='}:
        izq, _ = evaluar_con_tipo(nodo.hijos[0])
        der, _ = evaluar_con_tipo(nodo.hijos[1])

        izq_val = valor_numerico(izq)
        der_val = valor_numerico(der)

        if es_valor_desconocido(izq_val) or es_valor_desconocido(der_val):
            return ValorDesconocido("bool", f"comparison {nodo.tipo}"), "bool"

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

    if nodo.tipo in {'+', '-', '*', '/', '%'}:
        izq, tipo_izq = evaluar_con_tipo(nodo.hijos[0])
        der, tipo_der = evaluar_con_tipo(nodo.hijos[1])

        izq_num = valor_numerico(izq)
        der_num = valor_numerico(der)

        # El módulo solo debe operar con tipos enteros.
        if nodo.tipo == '%':
            if tipo_izq in REALES or tipo_der in REALES:
                error_semantico("modulo operator requires integer operands", nodo=nodo)

            if es_valor_desconocido(izq_num) or es_valor_desconocido(der_num):
                return ValorDesconocido("int", "modulo %"), "int"

            if der_num == 0:
                error_semantico("modulo by zero", nodo=nodo)

            return int(izq_num % der_num), "int"

        tipo_res = tipo_aritmetico(tipo_izq, tipo_der, nodo.tipo)

        # Si algún operando viene de parámetro o llamada a función,
        # no podemos calcular el valor real en SDT.
        # Solo propagamos el tipo resultante.
        if es_valor_desconocido(izq_num) or es_valor_desconocido(der_num):
            return ValorDesconocido(tipo_res, f"arithmetic {nodo.tipo}"), tipo_res

        if nodo.tipo == '+':
            valor = izq_num + der_num

        elif nodo.tipo == '-':
            valor = izq_num - der_num

        elif nodo.tipo == '*':
            valor = izq_num * der_num

        elif nodo.tipo == '/':
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
    if item.tipo == 'DECL_MATRIX_ITEM':
        return _declarar_matriz_item(tipo_dato, item)
    
    if item.tipo == 'DECL_ARRAY_ITEM':
        return _declarar_array_item(tipo_dato, item)
    
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


def parsear_string_literal(val, posiciones=None, indice=0):
    if not (isinstance(val, str) and len(val) >= 2 and val[0] == '"' and val[-1] == '"'):
        error_semantico(f"expected string literal, got '{val}'", posiciones, indice)

    contenido = val[1:-1]

    escapes = {
        "\\n": "\n",
        "\\t": "\t",
        "\\r": "\r",
        "\\0": "\0",
        '\\"': '"',
        "\\\\": "\\",
    }

    for escape, real in escapes.items():
        contenido = contenido.replace(escape, real)

    return ValorString(contenido)


def parsear_constante(val, posiciones=None, indice=0):
    if isinstance(val, (int, float, bool)):
        return val
    if isinstance(val, str):
        if val == "true":
            return True
        if val == "false":
            return False

        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
            return parsear_string_literal(val, posiciones, indice)

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

    if es_valor_desconocido(valor_actual):
        nuevo_valor = ValorDesconocido(tipo_var, f"{operador} {nombre_var}")
    else:
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


def declarar_parametros_funcion_actual(posiciones=None):
    funcion_actual = obtener_funcion_actual()

    if funcion_actual is None:
        return

    tabla_actual = obtener_tabla_actual()

    for param in funcion_actual['parametros']:
        nombre = param['nombre']
        tipo = param['tipo']

        tabla_actual.declarar(nombre, tipo, posiciones, 0)
        tabla_actual.asignar(
            nombre,
            ValorDesconocido(tipo, f"param {nombre}"),
            posiciones,
            0
        )


def validar_print_expr(expr_nodo):
    evaluarexpresion(expr_nodo, con_tipo=True)


def validar_printf_formato(formato_nodo):
    valor, tipo = evaluarexpresion(formato_nodo, con_tipo=True)

    if tipo != "string":
        error_semantico(
            "printf first argument must be a string literal",
            nodo=formato_nodo
        )

    return valor.valor


def validar_printf_args(formato_nodo, argumentos):
    formato = validar_printf_formato(formato_nodo)
    especificadores = extraer_formatos_printf(formato, formato_nodo)

    if len(especificadores) != len(argumentos):
        error_semantico(
            f"printf expects {len(especificadores)} argument(s), got {len(argumentos)}",
            nodo=formato_nodo
        )

    for indice, (especificador, arg) in enumerate(zip(especificadores, argumentos)):
        _, tipo_arg = evaluarexpresion(arg, con_tipo=True)

        if not tipo_compatible_printf(especificador, tipo_arg):
            error_semantico(
                f"printf argument {indice + 1} expects '%{especificador}' compatible type, got '{tipo_arg}'",
                nodo=arg
            )


def extraer_formatos_printf(formato, nodo=None):
    especificadores = []
    permitidos = {"d", "i", "u", "f", "c", "s", "b"}

    i = 0
    while i < len(formato):
        if formato[i] != "%":
            i += 1
            continue

        if i + 1 >= len(formato):
            error_semantico("incomplete printf format specifier", nodo=nodo)

        siguiente = formato[i + 1]

        # % imprime un porcentaje literal y no consume argumento
        if siguiente == "%":
            i += 2
            continue

        if siguiente not in permitidos:
            error_semantico(
                f"unsupported printf format specifier '%{siguiente}'",
                nodo=nodo
            )

        especificadores.append(siguiente)
        i += 2

    return especificadores


def tipo_compatible_printf(especificador, tipo):
    if especificador in {"d", "i"}:
        return tipo in ENTEROS | {"char", "bool"}

    if especificador == "u":
        return tipo in ENTEROS | {"char", "bool"}

    if especificador == "f":
        return tipo in ENTEROS | REALES | {"char", "bool"}

    if especificador == "c":
        return tipo in ENTEROS | {"char"}

    if especificador == "s":
        return tipo == "string"

    if especificador == "b":
        return tipo == "bool"

    return False


def validar_funcion_retorno(header):
    if header is None:
        return

    tipo_retorno = header['tipo_retorno']

    if tipo_retorno != "void" and not header.get('tiene_return', False):
        error_semantico(
            f"function '{header['nombre']}' must return a value of type '{tipo_retorno}'",
            nodo=Nodo(
                'FUNCTION',
                header['nombre'],
                linea=header['linea'],
                columna=header['columna']
            )
        )


def _evaluar_indice_array(indice_nodo):
    valor_indice, tipo_indice = evaluarexpresion(indice_nodo, con_tipo=True)

    if tipo_indice not in ENTEROS | {"char", "bool"}:
        error_semantico(
            f"array index must be integer-compatible, got '{tipo_indice}'",
            nodo=indice_nodo
        )

    if es_valor_desconocido(valor_indice):
        return valor_indice

    valor_indice = valor_numerico(valor_indice)

    if not isinstance(valor_indice, int):
        error_semantico("array index must be an integer", nodo=indice_nodo)

    return valor_indice


def _declarar_array_item(tipo_dato, item):
    nombre_var = item.valor
    tamano_nodo = item.hijos[0]
    init_nodo = item.hijos[1] if len(item.hijos) > 1 else None

    tamano_valor, tamano_tipo = evaluarexpresion(tamano_nodo, con_tipo=True)

    if tamano_tipo not in ENTEROS | {"char", "bool"}:
        error_semantico(
            f"array size for '{nombre_var}' must be integer-compatible",
            nodo=tamano_nodo
        )

    if es_valor_desconocido(tamano_valor):
        error_semantico(
            f"array size for '{nombre_var}' must be known at compile time",
            nodo=tamano_nodo
        )

    tamano = valor_numerico(tamano_valor)

    tabla_actual = obtener_tabla_actual()
    pos_item = [(item.linea, item.columna)] if item.linea is not None else None

    tabla_actual.declarar_array(nombre_var, tipo_dato, tamano, pos_item, 0)

    hijos_ast = [
        Nodo('TYPE', tipo_dato, linea=item.linea, columna=item.columna),
        tamano_nodo
    ]

    if init_nodo is not None:
        inicializadores = init_nodo.hijos

        if len(inicializadores) != tamano:
            error_semantico(
                f"array '{nombre_var}' expects {tamano} initializer(s), got {len(inicializadores)}",
                nodo=init_nodo
            )

        for indice_array, expr_nodo in enumerate(inicializadores):
            valor = evaluarexpresion(expr_nodo)

            tabla_actual.asignar_array(
                nombre_var,
                indice_array,
                valor,
                pos_item,
                0,
                nodo=expr_nodo
            )

        hijos_ast.append(init_nodo)

    return Nodo(
        'DECL_ARRAY',
        nombre_var,
        hijos_ast,
        linea=item.linea,
        columna=item.columna
    )


def _declarar_matriz_item(tipo_dato, item):
    nombre_var = item.valor
    filas_nodo = item.hijos[0]
    columnas_nodo = item.hijos[1]

    filas_valor, filas_tipo = evaluarexpresion(filas_nodo, con_tipo=True)
    columnas_valor, columnas_tipo = evaluarexpresion(columnas_nodo, con_tipo=True)

    if filas_tipo not in ENTEROS | {"char", "bool"}:
        error_semantico(
            f"matrix row size for '{nombre_var}' must be integer-compatible",
            nodo=filas_nodo
        )

    if columnas_tipo not in ENTEROS | {"char", "bool"}:
        error_semantico(
            f"matrix column size for '{nombre_var}' must be integer-compatible",
            nodo=columnas_nodo
        )

    if es_valor_desconocido(filas_valor) or es_valor_desconocido(columnas_valor):
        error_semantico(
            f"matrix dimensions for '{nombre_var}' must be known at compile time",
            nodo=item
        )

    filas = valor_numerico(filas_valor)
    columnas = valor_numerico(columnas_valor)

    tabla_actual = obtener_tabla_actual()
    pos_item = [(item.linea, item.columna)] if item.linea is not None else None

    tabla_actual.declarar_matriz(nombre_var, tipo_dato, filas, columnas, pos_item, 0)

    return Nodo(
        'DECL_MATRIX',
        nombre_var,
        [
            Nodo('TYPE', tipo_dato, linea=item.linea, columna=item.columna),
            filas_nodo,
            columnas_nodo
        ],
        linea=item.linea,
        columna=item.columna
    )


def _crear_array_access(nombre_var, indice_nodo, posiciones=None):
    linea, columna = _pos(posiciones, 0)

    return Nodo(
        'ARRAY_ACCESS',
        nombre_var,
        [indice_nodo],
        linea=linea,
        columna=columna
    )


def _crear_matrix_access(nombre_var, fila_nodo, columna_nodo, posiciones=None):
    linea, columna = _pos(posiciones, 0)

    return Nodo(
        'MATRIX_ACCESS',
        nombre_var,
        [fila_nodo, columna_nodo],
        linea=linea,
        columna=columna
    )


def _evaluar_array_access(nodo):
    nombre_var = nodo.valor
    indice_nodo = nodo.hijos[0]

    indice_valor = _evaluar_indice_array(indice_nodo)

    ambito, _ = buscar_variable(nombre_var)

    if ambito is None:
        error_semantico(f"array '{nombre_var}' not declared", nodo=nodo)

    return ambito.obtener_array(nombre_var, indice_valor, nodo=nodo)


def _evaluar_matrix_access(nodo):
    nombre_var = nodo.valor
    fila_nodo = nodo.hijos[0]
    columna_nodo = nodo.hijos[1]

    fila_valor = _evaluar_indice_array(fila_nodo)
    columna_valor = _evaluar_indice_array(columna_nodo)

    ambito, _ = buscar_variable(nombre_var)

    if ambito is None:
        error_semantico(f"matrix '{nombre_var}' not declared", nodo=nodo)

    return ambito.obtener_matriz(nombre_var, fila_valor, columna_valor, nodo=nodo)


def _asignar_array_access(array_nodo, expr_nodo, posiciones=None):
    nombre_var = array_nodo.valor
    indice_nodo = array_nodo.hijos[0]

    indice_valor = _evaluar_indice_array(indice_nodo)
    valor = evaluarexpresion(expr_nodo)

    ambito, _ = buscar_variable(nombre_var)

    if ambito is None:
        error_semantico(f"array '{nombre_var}' not declared", nodo=array_nodo)

    ambito.asignar_array(
        nombre_var,
        indice_valor,
        valor,
        posiciones,
        0,
        nodo=array_nodo
    )

    linea, columna = _pos(posiciones, 0)
    return Nodo(
        'ASSIGN_ARRAY',
        nombre_var,
        [indice_nodo, expr_nodo],
        linea=linea,
        columna=columna
    )


def _asignar_matrix_access(matrix_nodo, expr_nodo, posiciones=None):
    nombre_var = matrix_nodo.valor
    fila_nodo = matrix_nodo.hijos[0]
    columna_nodo = matrix_nodo.hijos[1]

    fila_valor = _evaluar_indice_array(fila_nodo)
    columna_valor = _evaluar_indice_array(columna_nodo)
    valor = evaluarexpresion(expr_nodo)

    ambito, _ = buscar_variable(nombre_var)

    if ambito is None:
        error_semantico(f"matrix '{nombre_var}' not declared", nodo=matrix_nodo)

    ambito.asignar_matriz(
        nombre_var,
        fila_valor,
        columna_valor,
        valor,
        posiciones,
        0,
        nodo=matrix_nodo
    )

    linea, columna = _pos(posiciones, 0)
    return Nodo(
        'ASSIGN_MATRIX',
        nombre_var,
        [fila_nodo, columna_nodo, expr_nodo],
        linea=linea,
        columna=columna
    )


def accion_semantica(produccion, elementos, posiciones=None):
    global funcion_pendiente
    
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

    elif lhs == "DeclItem" and rhs == ("ID", "[", "E", "]"):
        linea, columna = _pos(posiciones, 0)

        return Nodo(
            'DECL_ARRAY_ITEM',
            elementos[0],
            [elementos[2]],
            linea=linea,
            columna=columna
        )
    
    elif lhs == "DeclItem" and rhs == ("ID", "[", "E", "]", "[", "E", "]"):
        linea, columna = _pos(posiciones, 0)

        return Nodo(
            'DECL_MATRIX_ITEM',
            elementos[0],
            [elementos[2], elementos[5]],
            linea=linea,
            columna=columna
        )
    
    elif lhs == "DeclItem" and rhs == ("ID", "[", "E", "]", "=", "{", "InitList", "}"):
        linea, columna = _pos(posiciones, 0)

        init_list = Nodo(
            'INIT_LIST',
            None,
            elementos[6],
            linea=linea,
            columna=columna
        )

        return Nodo(
            'DECL_ARRAY_ITEM',
            elementos[0],
            [elementos[2], init_list],
            linea=linea,
            columna=columna
        )
    
    # Asignación
    elif lhs == "Assignment" and rhs == ("ID", "=", "E"):
        return _crear_asignacion(
            elementos[0],
            elementos[2],
            posiciones,
            aplicar=True
        )
    
    elif lhs == "Assignment" and rhs == ("ArrayAccess", "=", "E"):
        return _asignar_array_access(
            elementos[0],
            elementos[2],
            posiciones
        )
    
    elif lhs == "Assignment" and rhs == ("MatrixAccess", "=", "E"):
        return _asignar_matrix_access(
            elementos[0],
            elementos[2],
            posiciones
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
        '+', '-', '*', '/', '%'
    }:
        return _nodo_binario(rhs[1], elementos, posiciones)

    # Operador unario
    elif lhs == "UnaryExpr" and rhs == ("!", "UnaryExpr"):
        return _nodo_unario('!', elementos, posiciones)
    
    elif lhs == "UnaryExpr" and rhs == ("-", "UnaryExpr"):
        return _nodo_unario('NEG', elementos, posiciones)

    elif lhs == "UnaryExpr" and rhs == ("+", "UnaryExpr"):
        return _nodo_unario('POS', elementos, posiciones)

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
    
    elif lhs == "Primary" and rhs == ("FunctionCall",):
        return elementos[0]
    
    elif lhs == "Primary" and rhs == ("ArrayAccess",):
        return elementos[0]
    
    elif lhs == "Primary" and rhs == ("MatrixAccess",):
        return elementos[0]
    
    # Funciones
    elif lhs == "FunctionHeader" and rhs == ("TYPE", "ID", "(", ")"):
        tipo_retorno = normalizar_tipo(elementos[0], posiciones, 0)
        nombre_funcion = elementos[1]
        parametros = []

        tabla_funciones.declarar(nombre_funcion, tipo_retorno, parametros, posiciones, 1)

        linea, columna = _pos(posiciones, 1)

        header = {
            'nombre': nombre_funcion,
            'tipo_retorno': tipo_retorno,
            'parametros': parametros,
            'linea': linea,
            'columna': columna,
            'tiene_return': False
        }

        funcion_pendiente = header

        return header

    elif lhs == "FunctionHeader" and rhs == ("TYPE", "ID", "(", "ParamList", ")"):
        tipo_retorno = normalizar_tipo(elementos[0], posiciones, 0)
        nombre_funcion = elementos[1]
        parametros = elementos[3]

        tabla_funciones.declarar(nombre_funcion, tipo_retorno, parametros, posiciones, 1)

        linea, columna = _pos(posiciones, 1)

        header = {
            'nombre': nombre_funcion,
            'tipo_retorno': tipo_retorno,
            'parametros': parametros,
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
    
    elif lhs == "EnterParams" and rhs == tuple():
        declarar_parametros_funcion_actual(posiciones)
        return None

    elif lhs == "FunctionBody" and rhs == ("{", "EnterParams", "StatementList", "}"):
        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'BLOCK',
            None,
            _normalizar_lista_sentencias(elementos[2]),
            linea=linea,
            columna=columna
        )

    elif lhs == "FunctionBody" and rhs == ("{", "EnterParams", "}"):
        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'BLOCK',
            None,
            [],
            linea=linea,
            columna=columna
        )

    elif lhs == "FunctionDecl" and rhs == (
        "FunctionHeader", "EnterFunction", "FunctionBody", "ExitFunction"
    ):
        header = elementos[0]
        bloque = elementos[2]

        if header is None:
            return None

        validar_funcion_retorno(header)

        params_nodos = [
            Nodo(
                'PARAM',
                param['nombre'],
                [Nodo('TYPE', param['tipo'])]
            )
            for param in header['parametros']
        ]

        return Nodo(
            'FUNCTION',
            header['nombre'],
            [
                Nodo('RETURN_TYPE', header['tipo_retorno']),
                Nodo('PARAMS', None, params_nodos),
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
    
    # Llamadas a funciones
    elif lhs == "Statement" and rhs == ("FunctionCall", ";"):
        return elementos[0]

    elif lhs == "FunctionCall" and rhs == ("ID", "(", ")"):
        nombre_funcion = elementos[0]

        info_funcion = tabla_funciones.obtener(nombre_funcion, posiciones, 0)

        if len(info_funcion['parametros']) != 0:
            error_semantico(
                f"function '{nombre_funcion}' expects {len(info_funcion['parametros'])} argument(s), got 0",
                posiciones,
                0
            )

        linea, columna = _pos(posiciones, 0)

        return Nodo(
            'CALL',
            nombre_funcion,
            [],
            linea=linea,
            columna=columna
        )

    elif lhs == "FunctionCall" and rhs == ("ID", "(", "ArgList", ")"):
        nombre_funcion = elementos[0]
        argumentos = elementos[2]

        info_funcion = tabla_funciones.obtener(nombre_funcion, posiciones, 0)
        parametros = info_funcion['parametros']

        if len(argumentos) != len(parametros):
            error_semantico(
                f"function '{nombre_funcion}' expects {len(parametros)} argument(s), got {len(argumentos)}",
                posiciones,
                0
            )

        for indice, (arg_nodo, param) in enumerate(zip(argumentos, parametros)):
            valor_arg, tipo_arg = evaluarexpresion(arg_nodo, con_tipo=True)

            convertir_a_tipo(
                valor_arg,
                param['tipo'],
                f"argument {indice + 1} of function '{nombre_funcion}'",
                posiciones,
                0,
                nodo=arg_nodo
            )

        linea, columna = _pos(posiciones, 0)

        return Nodo(
            'CALL',
            nombre_funcion,
            argumentos,
            linea=linea,
            columna=columna
        )
    
    # Parámetros de función
    elif lhs == "Param" and rhs == ("TYPE", "ID"):
        tipo_param = normalizar_tipo(elementos[0], posiciones, 0)

        if tipo_param == "void":
            error_semantico(
                f"parameter '{elementos[1]}' cannot be void",
                posiciones,
                0
            )

        return {
            'tipo': tipo_param,
            'nombre': elementos[1]
        }

    elif lhs == "ParamList" and rhs == ("Param",):
        return [elementos[0]]

    elif lhs == "ParamList" and rhs == ("ParamList", ",", "Param"):
        return elementos[0] + [elementos[2]]
    
    # Argumentos de función (en llamadas)
    elif lhs == "ArgList" and rhs == ("E",):
        return [elementos[0]]

    elif lhs == "ArgList" and rhs == ("ArgList", ",", "E"):
        return elementos[0] + [elementos[2]]

    # Print/Printf
    elif lhs == "Statement" and rhs == ("PrintStatement", ";"):
        return elementos[0]

    elif lhs == "PrintStatement" and rhs == ("print", "(", "E", ")"):
        expr = elementos[2]

        validar_print_expr(expr)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'PRINT',
            None,
            [expr],
            linea=linea,
            columna=columna
        )

    elif lhs == "PrintStatement" and rhs == ("printf", "(", "CONST", ")"):
        linea_const, columna_const = _pos(posiciones, 2)

        formato = Nodo(
            'CONST',
            parsear_constante(elementos[2], posiciones, 2),
            linea=linea_const,
            columna=columna_const
        )

        validar_printf_args(formato, [])

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'PRINTF',
            None,
            [formato],
            linea=linea,
            columna=columna
        )

    elif lhs == "PrintStatement" and rhs == ("printf", "(", "CONST", ",", "ArgList", ")"):
        linea_const, columna_const = _pos(posiciones, 2)

        formato = Nodo(
            'CONST',
            parsear_constante(elementos[2], posiciones, 2),
            linea=linea_const,
            columna=columna_const
        )

        argumentos = elementos[4]

        validar_printf_args(formato, argumentos)

        linea, columna = _pos(posiciones, 0)
        return Nodo(
            'PRINTF',
            None,
            [formato] + argumentos,
            linea=linea,
            columna=columna
        )

    #Arrays
    elif lhs == "ArrayAccess" and rhs == ("ID", "[", "E", "]"):
        return _crear_array_access(
            elementos[0],
            elementos[2],
            posiciones
    )

    elif lhs == "InitList" and rhs == ("E",):
        return [elementos[0]]

    elif lhs == "InitList" and rhs == ("InitList", ",", "E"):
        return elementos[0] + [elementos[2]]

    # Matrices
    elif lhs == "MatrixAccess" and rhs == ("ID", "[", "E", "]", "[", "E", "]"):
        return _crear_matrix_access(
            elementos[0],
            elementos[2],
            elementos[5],
            posiciones
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
