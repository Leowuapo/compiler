# PENTA Compiler - documentación interna
# Tablas semánticas: administra variables, arreglos, matrices y funciones por ámbito.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

from .errors import error_semantico
from .types import convertir_a_tipo, normalizar_tipo
from .values import ValorDesconocido, es_valor_desconocido, formatear_valor


# Controla variables, arreglos y matrices declaradas dentro de un ámbito.
class TablaSimbolos:
    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def __init__(self):
        self.simbolos = {}

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def limpiar(self):
        self.simbolos = {}

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def declarar(self, nombre, tipo, posiciones=None, indice=0):
        tipo = normalizar_tipo(tipo, posiciones, indice)
        if tipo == "void":
            error_semantico(f"variable '{nombre}' cannot be declared as void", posiciones, indice)
        if nombre in self.simbolos:
            error_semantico(f"variable '{nombre}' already declared", posiciones, indice)
        self.simbolos[nombre] = {'tipo': tipo, 'valor': None}

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def asignar(self, nombre, valor, posiciones=None, indice=0):
        if nombre not in self.simbolos:
            error_semantico(f"variable '{nombre}' not declared", posiciones, indice)
        tipo_destino = self.simbolos[nombre]['tipo']
        self.simbolos[nombre]['valor'] = convertir_a_tipo(
            valor, tipo_destino, nombre, posiciones, indice
        )

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def obtener(self, nombre, posiciones=None, indice=0):
        if nombre not in self.simbolos:
            error_semantico(f"variable '{nombre}' not declared", posiciones, indice)
        return self.simbolos[nombre]

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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
    
    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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
    
    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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
    
# Controla firmas de funciones, tipos de retorno y parámetros declarados.
class TablaFunciones:
    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def __init__(self):
        self.funciones = {}

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def limpiar(self):
        self.funciones = {}

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
    def obtener(self, nombre, posiciones=None, indice=0):
        if nombre not in self.funciones:
            error_semantico(f"function '{nombre}' not declared", posiciones, indice)

        return self.funciones[nombre]

    # Opera sobre la tabla semántica cuidando tipos, rangos y existencia de símbolos.
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
