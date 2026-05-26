from dataclasses import dataclass


@dataclass
class TACInstruction:
    op: str
    arg1: object = None
    arg2: object = None
    result: object = None

    def __str__(self):
        if self.op == "LABEL":
            return f"{self.result}:"

        if self.op == "FUNC":
            return f"func {self.result}:"

        if self.op == "END_FUNC":
            return f"end func {self.result}"

        if self.op == "PARAM":
            return f"param {self.result}"

        if self.op == "ARG":
            return f"arg {self.result}"

        if self.op == "CALL":
            if self.result is None:
                return f"call {self.arg1}, {self.arg2}"
            return f"{self.result} = call {self.arg1}, {self.arg2}"

        if self.op == "RETURN":
            if self.result is None:
                return "return"
            return f"return {self.result}"

        if self.op == "GOTO":
            return f"goto {self.result}"

        if self.op == "IF_FALSE":
            return f"ifFalse {self.arg1} goto {self.result}"

        if self.op == "IF_TRUE":
            return f"if {self.arg1} goto {self.result}"

        if self.op == "ASSIGN":
            return f"{self.result} = {self.arg1}"

        if self.op in {"+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"}:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"

        if self.op in {"NEG", "POS", "!"}:
            simbolo = "-" if self.op == "NEG" else "+" if self.op == "POS" else "!"
            return f"{self.result} = {simbolo}{self.arg1}"

        if self.op == "PRINT":
            return f"print {self.result}"

        if self.op == "PRINTF":
            args = ", ".join(map(str, self.arg2 or []))
            if args:
                return f"printf {self.arg1}, {args}"
            return f"printf {self.arg1}"

        if self.op == "LOAD_ARRAY":
            return f"{self.result} = {self.arg1}[{self.arg2}]"

        if self.op == "STORE_ARRAY":
            nombre, indice = self.result
            return f"{nombre}[{indice}] = {self.arg1}"

        if self.op == "LOAD_MATRIX":
            nombre, fila, columna = self.arg1
            return f"{self.result} = {nombre}[{fila}][{columna}]"

        if self.op == "STORE_MATRIX":
            nombre, fila, columna = self.result
            return f"{nombre}[{fila}][{columna}] = {self.arg1}"

        """
        if self.op == "DECL":
            return f"decl {self.result}"

        if self.op == "DECL_ARRAY":
            return f"decl_array {self.result}[{self.arg1}]"

        if self.op == "DECL_MATRIX":
            filas, columnas = self.arg1
            return f"decl_matrix {self.result}[{filas}][{columnas}]"
        """
        return f"{self.op} {self.arg1} {self.arg2} {self.result}"
        


class TACGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0
        self.break_stack = []
        self.continue_stack = []

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self, prefix="L"):
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def emit(self, op, arg1=None, arg2=None, result=None):
        instr = TACInstruction(op, arg1, arg2, result)
        self.instructions.append(instr)
        return instr

    def generate(self, ast):
        self.visit(ast)
        return self.instructions

    def visit(self, nodo):
        if nodo is None:
            return None

        if isinstance(nodo, list):
            for item in nodo:
                self.visit(item)
            return None

        metodo = getattr(self, f"visit_{nodo.tipo}", self.visit_default)
        return metodo(nodo)

    def visit_default(self, nodo):
        for hijo in getattr(nodo, "hijos", []):
            self.visit(hijo)
        return None

    # -------------------------
    # Programa / funciones
    # -------------------------

    def visit_PROGRAM(self, nodo):
        for hijo in nodo.hijos:
            self.visit(hijo)

    def visit_FUNCTION(self, nodo):
        nombre = nodo.valor
        self.emit("FUNC", result=nombre)

        params_node = None
        body_node = None

        for hijo in nodo.hijos:
            if hijo.tipo == "PARAMS":
                params_node = hijo
            elif hijo.tipo == "BLOCK":
                body_node = hijo

        if params_node is not None:
            for param in params_node.hijos:
                self.emit("PARAM", result=param.valor)

        if body_node is not None:
            self.visit(body_node)

        self.emit("END_FUNC", result=nombre)

    def visit_BLOCK(self, nodo):
        for stmt in nodo.hijos:
            self.visit(stmt)

    def visit_STMT_LIST(self, nodo):
        for stmt in nodo.hijos:
            self.visit(stmt)

    # -------------------------
    # Declaraciones / asignación
    # -------------------------

    def visit_DECL_LIST(self, nodo):
        for decl in nodo.hijos:
            self.visit(decl)

    def visit_DECL(self, nodo):
        nombre = nodo.valor

        # En TAC puro no emitimos declaración.
        # Solo emitimos asignación si la variable tiene inicializador.
        if len(nodo.hijos) > 1:
            valor = self.gen_expr(nodo.hijos[1])
            self.emit("ASSIGN", arg1=valor, result=nombre)

    def visit_DECL_ARRAY(self, nodo):
        nombre = nodo.valor

        # En TAC puro no emitimos decl_array.
        # Si existe inicializador, solo generamos stores.
        if len(nodo.hijos) > 2 and nodo.hijos[2].tipo == "INIT_LIST":
            for indice, expr in enumerate(nodo.hijos[2].hijos):
                valor = self.gen_expr(expr)
                self.emit("STORE_ARRAY", arg1=valor, result=(nombre, indice))

    def visit_DECL_MATRIX(self, nodo):
        # En TAC puro no emitimos declaración de matriz.
        # Las asignaciones/accesos posteriores generarán STORE_MATRIX / LOAD_MATRIX.
        return None

    def visit_ASSIGN(self, nodo):
        valor = self.gen_expr(nodo.hijos[0])
        self.emit("ASSIGN", arg1=valor, result=nodo.valor)

    def visit_ASSIGN_ARRAY(self, nodo):
        nombre = nodo.valor
        indice = self.gen_expr(nodo.hijos[0])
        valor = self.gen_expr(nodo.hijos[1])
        self.emit("STORE_ARRAY", arg1=valor, result=(nombre, indice))

    def visit_ASSIGN_MATRIX(self, nodo):
        nombre = nodo.valor
        fila = self.gen_expr(nodo.hijos[0])
        columna = self.gen_expr(nodo.hijos[1])
        valor = self.gen_expr(nodo.hijos[2])
        self.emit("STORE_MATRIX", arg1=valor, result=(nombre, fila, columna))

    # -------------------------
    # Control flow
    # -------------------------

    def visit_IF(self, nodo):
        condicion = self.gen_expr(nodo.hijos[0])
        label_end = self.new_label("endif")

        self.emit("IF_FALSE", arg1=condicion, result=label_end)
        self.visit(nodo.hijos[1])
        self.emit("LABEL", result=label_end)

    def visit_IF_ELSE(self, nodo):
        condicion = self.gen_expr(nodo.hijos[0])
        label_else = self.new_label("else")
        label_end = self.new_label("endif")

        self.emit("IF_FALSE", arg1=condicion, result=label_else)
        self.visit(nodo.hijos[1])
        self.emit("GOTO", result=label_end)
        self.emit("LABEL", result=label_else)
        self.visit(nodo.hijos[2])
        self.emit("LABEL", result=label_end)

    def visit_WHILE(self, nodo):
        label_start = self.new_label("while")
        label_end = self.new_label("endwhile")

        self.emit("LABEL", result=label_start)

        condicion = self.gen_expr(nodo.hijos[0])
        self.emit("IF_FALSE", arg1=condicion, result=label_end)

        self.break_stack.append(label_end)
        self.continue_stack.append(label_start)

        self.visit(nodo.hijos[1])

        self.continue_stack.pop()
        self.break_stack.pop()

        self.emit("GOTO", result=label_start)
        self.emit("LABEL", result=label_end)

    def visit_FOR(self, nodo):
        init = nodo.hijos[0]
        condicion_nodo = nodo.hijos[1]
        update = nodo.hijos[2]
        bloque = nodo.hijos[3]

        label_start = self.new_label("for")
        label_update = self.new_label("for_update")
        label_end = self.new_label("endfor")

        self.visit(init)

        self.emit("LABEL", result=label_start)
        condicion = self.gen_expr(condicion_nodo)
        self.emit("IF_FALSE", arg1=condicion, result=label_end)

        self.break_stack.append(label_end)
        self.continue_stack.append(label_update)

        self.visit(bloque)

        self.continue_stack.pop()
        self.break_stack.pop()

        self.emit("LABEL", result=label_update)
        self.visit(update)
        self.emit("GOTO", result=label_start)
        self.emit("LABEL", result=label_end)

    def visit_SWITCH(self, nodo):
        expr_switch = self.gen_expr(nodo.hijos[0])

        cases = [h for h in nodo.hijos[1:] if h.tipo == "CASE"]
        default = next((h for h in nodo.hijos[1:] if h.tipo == "DEFAULT"), None)

        label_end = self.new_label("endswitch")
        label_default = self.new_label("default") if default is not None else label_end

        case_labels = []

        for case in cases:
            label_case = self.new_label("case")
            case_labels.append((case, label_case))

            valor_case = self.gen_expr(case.hijos[0])
            temp_cmp = self.new_temp()
            self.emit("==", arg1=expr_switch, arg2=valor_case, result=temp_cmp)
            self.emit("IF_TRUE", arg1=temp_cmp, result=label_case)

        self.emit("GOTO", result=label_default)

        self.break_stack.append(label_end)

        for case, label_case in case_labels:
            self.emit("LABEL", result=label_case)
            self.visit(case.hijos[1])

            # Evita fall-through automático hacia el siguiente case.
            # Si el bloque ya terminó con goto por break, no duplicamos.
            if not self.instructions or self.instructions[-1].op != "GOTO":
                self.emit("GOTO", result=label_end)

        if default is not None:
            self.emit("LABEL", result=label_default)
            self.visit(default.hijos[0])

            if not self.instructions or self.instructions[-1].op != "GOTO":
                self.emit("GOTO", result=label_end)

        self.break_stack.pop()

        self.emit("LABEL", result=label_end)

    def visit_BREAK(self, nodo):
        if not self.break_stack:
            raise Exception("TAC error: break outside loop/switch")
        self.emit("GOTO", result=self.break_stack[-1])

    def visit_CONTINUE(self, nodo):
        if not self.continue_stack:
            raise Exception("TAC error: continue outside loop")
        self.emit("GOTO", result=self.continue_stack[-1])

    # -------------------------
    # Funciones / llamadas / return
    # -------------------------

    def visit_RETURN(self, nodo):
        if nodo.hijos:
            valor = self.gen_expr(nodo.hijos[0])
            self.emit("RETURN", result=valor)
        else:
            self.emit("RETURN")

    def visit_CALL(self, nodo):
        # llamada como statement
        for arg in nodo.hijos:
            valor_arg = self.gen_expr(arg)
            self.emit("ARG", result=valor_arg)

        self.emit("CALL", arg1=nodo.valor, arg2=len(nodo.hijos), result=None)

    # -------------------------
    # Print / printf
    # -------------------------

    def visit_PRINT(self, nodo):
        valor = self.gen_expr(nodo.hijos[0])
        self.emit("PRINT", result=valor)

    def visit_PRINTF(self, nodo):
        formato = self.gen_expr(nodo.hijos[0])
        args = [self.gen_expr(arg) for arg in nodo.hijos[1:]]
        self.emit("PRINTF", arg1=formato, arg2=args)

    # -------------------------
    # Expresiones
    # -------------------------

    def gen_expr(self, nodo):
        if nodo is None:
            return None

        if nodo.tipo == "CONST":
            return self.format_const(nodo.valor)

        if nodo.tipo == "ID":
            return nodo.valor

        if nodo.tipo == "ARRAY_ACCESS":
            indice = self.gen_expr(nodo.hijos[0])
            temp = self.new_temp()
            self.emit("LOAD_ARRAY", arg1=nodo.valor, arg2=indice, result=temp)
            return temp

        if nodo.tipo == "MATRIX_ACCESS":
            fila = self.gen_expr(nodo.hijos[0])
            columna = self.gen_expr(nodo.hijos[1])
            temp = self.new_temp()
            self.emit("LOAD_MATRIX", arg1=(nodo.valor, fila, columna), result=temp)
            return temp

        if nodo.tipo == "CALL":
            for arg in nodo.hijos:
                valor_arg = self.gen_expr(arg)
                self.emit("ARG", result=valor_arg)

            temp = self.new_temp()
            self.emit("CALL", arg1=nodo.valor, arg2=len(nodo.hijos), result=temp)
            return temp

        if nodo.tipo in {"+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"}:
            izq = self.gen_expr(nodo.hijos[0])
            der = self.gen_expr(nodo.hijos[1])
            temp = self.new_temp()
            self.emit(nodo.tipo, arg1=izq, arg2=der, result=temp)
            return temp

        if nodo.tipo in {"NEG", "POS", "!"}:
            valor = self.gen_expr(nodo.hijos[0])
            temp = self.new_temp()
            self.emit(nodo.tipo, arg1=valor, result=temp)
            return temp

        raise Exception(f"TAC error: expression node not supported: {nodo.tipo}")

    def format_const(self, valor):
        # ValorString de sdt.py tiene atributo .valor
        if hasattr(valor, "valor"):
            return repr(valor.valor)

        if isinstance(valor, str):
            return repr(valor)

        if isinstance(valor, bool):
            return "true" if valor else "false"

        return valor


def generar_tac(ast):
    generator = TACGenerator()
    return generator.generate(ast)


def imprimir_tac(instrucciones):
    for i, instr in enumerate(instrucciones):
        print(f"{i:04d}: {instr}")


def guardar_tac(instrucciones, ruta="tac.ir"):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for instr in instrucciones:
            archivo.write(str(instr) + "\n")