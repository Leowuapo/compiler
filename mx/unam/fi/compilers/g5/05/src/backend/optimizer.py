# PENTA Compiler - documentación interna
# Optimización de TAC: aplica propagación de constantes/copias, simplificación algebraica y eliminación segura de temporales muertos.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

from .tac import TACInstruction


BIN_OPS = {
    "+", "-", "*", "/", "%",
    "==", "!=", "<", ">", "<=", ">=",
    "&&", "||"
}

UNARY_OPS = {"NEG", "POS", "!"}

CONTROL_OPS = {"GOTO", "IF_FALSE", "IF_TRUE", "RETURN"}
BARRIER_OPS = {"FUNC", "END_FUNC", "LABEL"}


# ------------------------------------------------------------
# Utilidades generales
# ------------------------------------------------------------

# Valida una condición pequeña usada por el flujo principal sin modificar estado.
def _is_temp(value):
    return isinstance(value, str) and value.startswith("t") and value[1:].isdigit()


# Valida una condición pequeña usada por el flujo principal sin modificar estado.
def _is_quoted_literal(value):
    if not isinstance(value, str):
        return False

    return (
        len(value) >= 2
        and (
            (value[0] == "'" and value[-1] == "'")
            or (value[0] == '"' and value[-1] == '"')
        )
    )


# Valida una condición pequeña usada por el flujo principal sin modificar estado.
def _is_bool_text(value):
    return value in {"true", "false"}


# Valida una condición pequeña usada por el flujo principal sin modificar estado.
def _is_variable_name(value):
    if not isinstance(value, str):
        return False

    if _is_quoted_literal(value):
        return False

    if _is_bool_text(value):
        return False

    return True


# Interpreta texto o instrucciones y las convierte a una estructura más útil.
def _parse_literal(value):
    if isinstance(value, (int, float, bool)):
        return value

    if value == "true":
        return True

    if value == "false":
        return False

    return value


# Valida una condición pequeña usada por el flujo principal sin modificar estado.
def _is_constant(value):
    parsed = _parse_literal(value)

    if isinstance(parsed, (int, float, bool)):
        return True

    if _is_quoted_literal(parsed):
        return True

    return False


# Valida una condición pequeña usada por el flujo principal sin modificar estado.
def _is_numeric_or_bool_constant(value):
    parsed = _parse_literal(value)
    return isinstance(parsed, (int, float, bool))


# Valida una condición pequeña usada por el flujo principal sin modificar estado.
def _is_truthy_constant(value):
    parsed = _parse_literal(value)

    if isinstance(parsed, (int, float, bool)):
        return bool(parsed)

    return None


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _clone(instr, **changes):
    data = {
        "op": instr.op,
        "arg1": instr.arg1,
        "arg2": instr.arg2,
        "result": instr.result,
    }

    data.update(changes)

    return TACInstruction(
        data["op"],
        data["arg1"],
        data["arg2"],
        data["result"]
    )


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _resolve(value, env):
    """
    Resuelve propagación de constantes/copias.

    Ejemplo:
        env["t1"] = 12
        env["x"] = "t1"

        _resolve("x", env) -> 12
    """
    current = value
    visited = set()

    while _is_variable_name(current) and current in env:
        if current in visited:
            break

        visited.add(current)
        current = env[current]

    return current


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _kill_name(env, name):
    """
    Si una variable se redefine, invalidamos:
    - su propio valor conocido
    - copias que dependían de ella

    Ejemplo:
        t1 = x
        x = 10

    Después de redefinir x, no podemos reemplazar t1 por x.
    """
    if not _is_variable_name(name):
        return

    for key, value in list(env.items()):
        if key == name or value == name:
            del env[key]


# ------------------------------------------------------------
# Usos y definiciones para dead temporary elimination
# ------------------------------------------------------------

# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _add_use(uses, value):
    if _is_variable_name(value):
        uses.add(value)


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _add_uses_from_tuple(uses, value_tuple):
    if not isinstance(value_tuple, tuple):
        return

    for item in value_tuple:
        _add_use(uses, item)


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _uses(instr):
    uses = set()

    if instr.op == "ASSIGN":
        _add_use(uses, instr.arg1)

    elif instr.op in BIN_OPS:
        _add_use(uses, instr.arg1)
        _add_use(uses, instr.arg2)

    elif instr.op in UNARY_OPS:
        _add_use(uses, instr.arg1)

    elif instr.op in {"IF_FALSE", "IF_TRUE"}:
        _add_use(uses, instr.arg1)

    elif instr.op == "RETURN":
        _add_use(uses, instr.result)

    elif instr.op == "ARG":
        _add_use(uses, instr.result)

    elif instr.op == "PRINT":
        _add_use(uses, instr.result)

    elif instr.op == "PRINTF":
        _add_use(uses, instr.arg1)

        for arg in instr.arg2 or []:
            _add_use(uses, arg)

    elif instr.op == "LOAD_ARRAY":
        # arg1 es nombre del arreglo, arg2 es índice
        _add_use(uses, instr.arg2)

    elif instr.op == "STORE_ARRAY":
        # result = (nombre, indice)
        _add_use(uses, instr.arg1)

        if isinstance(instr.result, tuple) and len(instr.result) >= 2:
            _add_use(uses, instr.result[1])

    elif instr.op == "LOAD_MATRIX":
        # arg1 = (nombre, fila, columna)
        if isinstance(instr.arg1, tuple) and len(instr.arg1) == 3:
            _, fila, columna = instr.arg1
            _add_use(uses, fila)
            _add_use(uses, columna)

    elif instr.op == "STORE_MATRIX":
        # result = (nombre, fila, columna)
        _add_use(uses, instr.arg1)

        if isinstance(instr.result, tuple) and len(instr.result) == 3:
            _, fila, columna = instr.result
            _add_use(uses, fila)
            _add_use(uses, columna)

    return uses


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _defs(instr):
    if instr.op in BIN_OPS | UNARY_OPS:
        return {instr.result} if _is_variable_name(instr.result) else set()

    if instr.op == "ASSIGN":
        return {instr.result} if _is_variable_name(instr.result) else set()

    if instr.op == "LOAD_ARRAY":
        return {instr.result} if _is_variable_name(instr.result) else set()

    if instr.op == "LOAD_MATRIX":
        return {instr.result} if _is_variable_name(instr.result) else set()

    if instr.op == "CALL":
        return {instr.result} if _is_variable_name(instr.result) else set()

    return set()


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _has_side_effect(instr):
    return instr.op in {
        "FUNC", "END_FUNC", "LABEL",
        "GOTO", "IF_FALSE", "IF_TRUE",
        "RETURN",
        "ARG", "CALL",
        "PRINT", "PRINTF",
        "STORE_ARRAY", "STORE_MATRIX",
        "PARAM"
    }


# ------------------------------------------------------------
# Constant folding y algebraic simplification
# ------------------------------------------------------------

# Evalúa operandos o expresiones internas durante la ejecución de la VM.
def _eval_binary(op, arg1, arg2):
    a = _parse_literal(arg1)
    b = _parse_literal(arg2)

    if not isinstance(a, (int, float, bool)):
        return None

    if not isinstance(b, (int, float, bool)):
        return None

    try:
        if op == "+":
            return a + b

        if op == "-":
            return a - b

        if op == "*":
            return a * b

        if op == "/":
            if b == 0:
                return None

            if isinstance(a, int) and isinstance(b, int):
                return int(a / b)

            return a / b

        if op == "%":
            if b == 0:
                return None

            return int(a % b)

        if op == "==":
            return a == b

        if op == "!=":
            return a != b

        if op == "<":
            return a < b

        if op == ">":
            return a > b

        if op == "<=":
            return a <= b

        if op == ">=":
            return a >= b

        if op == "&&":
            return bool(a) and bool(b)

        if op == "||":
            return bool(a) or bool(b)

    except Exception:
        return None

    return None


# Evalúa operandos o expresiones internas durante la ejecución de la VM.
def _eval_unary(op, arg):
    value = _parse_literal(arg)

    if not isinstance(value, (int, float, bool)):
        return None

    if op == "NEG":
        return -value

    if op == "POS":
        return +value

    if op == "!":
        return not bool(value)

    return None


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _simplify_algebraic(instr):
    op = instr.op
    a = _parse_literal(instr.arg1)
    b = _parse_literal(instr.arg2)
    r = instr.result

    if op == "+":
        if b == 0:
            return TACInstruction("ASSIGN", arg1=instr.arg1, result=r)
        if a == 0:
            return TACInstruction("ASSIGN", arg1=instr.arg2, result=r)

    if op == "-":
        if b == 0:
            return TACInstruction("ASSIGN", arg1=instr.arg1, result=r)

    if op == "*":
        if b == 1:
            return TACInstruction("ASSIGN", arg1=instr.arg1, result=r)
        if a == 1:
            return TACInstruction("ASSIGN", arg1=instr.arg2, result=r)
        if a == 0 or b == 0:
            return TACInstruction("ASSIGN", arg1=0, result=r)

    if op == "/":
        if b == 1:
            return TACInstruction("ASSIGN", arg1=instr.arg1, result=r)

    if op == "%":
        if b == 1:
            return TACInstruction("ASSIGN", arg1=0, result=r)

    if op == "&&":
        if a is True:
            return TACInstruction("ASSIGN", arg1=instr.arg2, result=r)
        if b is True:
            return TACInstruction("ASSIGN", arg1=instr.arg1, result=r)
        if a is False or b is False:
            return TACInstruction("ASSIGN", arg1=False, result=r)

    if op == "||":
        if a is False:
            return TACInstruction("ASSIGN", arg1=instr.arg2, result=r)
        if b is False:
            return TACInstruction("ASSIGN", arg1=instr.arg1, result=r)
        if a is True or b is True:
            return TACInstruction("ASSIGN", arg1=True, result=r)

    return instr


# Aplica constant folding y simplificaciones algebraicas a una instrucción.
def fold_and_simplify_instruction(instr):
    if instr.op in BIN_OPS:
        folded = _eval_binary(instr.op, instr.arg1, instr.arg2)

        if folded is not None:
            return TACInstruction("ASSIGN", arg1=folded, result=instr.result)

        return _simplify_algebraic(instr)

    if instr.op in UNARY_OPS:
        folded = _eval_unary(instr.op, instr.arg1)

        if folded is not None:
            return TACInstruction("ASSIGN", arg1=folded, result=instr.result)

    return instr


# ------------------------------------------------------------
# Sustitución de operandos
# ------------------------------------------------------------

# Reemplaza operandos por valores conocidos cuando es seguro hacerlo.
def substitute_operands(instr, env):
    if instr.op == "ASSIGN":
        return _clone(instr, arg1=_resolve(instr.arg1, env))

    if instr.op in BIN_OPS:
        return _clone(
            instr,
            arg1=_resolve(instr.arg1, env),
            arg2=_resolve(instr.arg2, env)
        )

    if instr.op in UNARY_OPS:
        return _clone(instr, arg1=_resolve(instr.arg1, env))

    if instr.op in {"IF_FALSE", "IF_TRUE"}:
        return _clone(instr, arg1=_resolve(instr.arg1, env))

    if instr.op == "RETURN":
        return _clone(instr, result=_resolve(instr.result, env))

    if instr.op == "ARG":
        return _clone(instr, result=_resolve(instr.result, env))

    if instr.op == "PRINT":
        return _clone(instr, result=_resolve(instr.result, env))

    if instr.op == "PRINTF":
        args = [_resolve(arg, env) for arg in (instr.arg2 or [])]
        return _clone(instr, arg1=_resolve(instr.arg1, env), arg2=args)

    if instr.op == "LOAD_ARRAY":
        return _clone(instr, arg2=_resolve(instr.arg2, env))

    if instr.op == "STORE_ARRAY":
        if isinstance(instr.result, tuple) and len(instr.result) == 2:
            nombre, indice = instr.result
            return _clone(
                instr,
                arg1=_resolve(instr.arg1, env),
                result=(nombre, _resolve(indice, env))
            )

        return _clone(instr, arg1=_resolve(instr.arg1, env))

    if instr.op == "LOAD_MATRIX":
        if isinstance(instr.arg1, tuple) and len(instr.arg1) == 3:
            nombre, fila, columna = instr.arg1
            return _clone(
                instr,
                arg1=(nombre, _resolve(fila, env), _resolve(columna, env))
            )

        return instr

    if instr.op == "STORE_MATRIX":
        if isinstance(instr.result, tuple) and len(instr.result) == 3:
            nombre, fila, columna = instr.result
            return _clone(
                instr,
                arg1=_resolve(instr.arg1, env),
                result=(nombre, _resolve(fila, env), _resolve(columna, env))
            )

        return _clone(instr, arg1=_resolve(instr.arg1, env))

    return instr


# ------------------------------------------------------------
# Constant propagation / copy propagation / branch simplification
# ------------------------------------------------------------

# Actualiza la interfaz o el estado interno después de un cambio relevante.
def _update_env_from_instruction(instr, env):
    if instr.op == "CALL":
        # Una llamada puede tener efectos secundarios. Conservador:
        # limpiamos el entorno para no propagar valores inválidos.
        env.clear()

        if instr.result:
            _kill_name(env, instr.result)

        return

    defs = _defs(instr)

    for name in defs:
        _kill_name(env, name)

    if instr.op == "ASSIGN" and _is_variable_name(instr.result):
        value = instr.arg1

        # Propagamos constantes para variables y temporales.
        if _is_constant(value):
            env[instr.result] = value
            return

        if _is_variable_name(value) and _is_temp(instr.result):
            if value != instr.result:
                env[instr.result] = value


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def optimize_branches(instr):
    if instr.op == "IF_FALSE":
        truth = _is_truthy_constant(instr.arg1)

        if truth is True:
            # ifFalse true goto L nunca salta
            return None

        if truth is False:
            # ifFalse false goto L siempre salta
            return TACInstruction("GOTO", result=instr.result)

    if instr.op == "IF_TRUE":
        truth = _is_truthy_constant(instr.arg1)

        if truth is True:
            # if true goto L siempre salta
            return TACInstruction("GOTO", result=instr.result)

        if truth is False:
            # if false goto L nunca salta
            return None

    return instr


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def constant_and_copy_propagation(instructions):
    optimized = []
    env = {}

    for instr in instructions:
        if instr.op in BARRIER_OPS:
            env.clear()
            optimized.append(instr)
            continue

        substituted = substitute_operands(instr, env)
        folded = fold_and_simplify_instruction(substituted)
        branched = optimize_branches(folded)

        if branched is None:
            continue

        optimized.append(branched)
        _update_env_from_instruction(branched, env)

        if branched.op in CONTROL_OPS:
            env.clear()

    return optimized


# ------------------------------------------------------------
# Limpieza de código muerto y saltos
# ------------------------------------------------------------

# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def remove_dead_code_after_jumps(instructions):
    optimized = []
    unreachable = False

    for instr in instructions:
        if instr.op in {"LABEL", "END_FUNC", "FUNC"}:
            unreachable = False
            optimized.append(instr)
            continue

        if unreachable:
            continue

        optimized.append(instr)

        if instr.op in {"GOTO", "RETURN"}:
            unreachable = True

    return optimized


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def remove_redundant_gotos(instructions):
    optimized = []

    i = 0

    while i < len(instructions):
        instr = instructions[i]

        if (
            instr.op == "GOTO"
            and i + 1 < len(instructions)
            and instructions[i + 1].op == "LABEL"
            and instructions[i + 1].result == instr.result
        ):
            i += 1
            continue

        optimized.append(instr)
        i += 1

    return optimized


# Quita etiquetas que no son destino de ningún salto.
def remove_unused_labels(instructions):
    used_labels = set()

    for instr in instructions:
        if instr.op in {"GOTO", "IF_FALSE", "IF_TRUE"}:
            used_labels.add(instr.result)

    optimized = []

    for instr in instructions:
        if instr.op == "LABEL" and instr.result not in used_labels:
            continue

        optimized.append(instr)

    return optimized


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def remove_redundant_assignments(instructions):
    optimized = []

    for instr in instructions:
        if instr.op == "ASSIGN" and instr.result == instr.arg1:
            continue

        optimized.append(instr)

    return optimized


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def remove_dead_temporaries(instructions):
    """
    Elimina asignaciones a temporales que nunca se usan.

    Ejemplo:
        t1 = 12
        x = 14

    Si t1 ya no aparece en ninguna instrucción posterior, se elimina.
    """

    live = set()
    reversed_optimized = []

    for instr in reversed(instructions):
        defs = _defs(instr)
        uses = _uses(instr)

        removable = (
            not _has_side_effect(instr)
            and len(defs) == 1
            and all(_is_temp(d) for d in defs)
            and defs.isdisjoint(live)
        )

        if removable:
            continue

        live -= defs
        live |= uses

        reversed_optimized.append(instr)

    return list(reversed(reversed_optimized))


# ------------------------------------------------------------
# Pipeline principal
# ------------------------------------------------------------
# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _as_int_constant(value):
    value = _parse_literal(value)

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    return None


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _value_contains_temp(value):
    if _is_temp(value):
        return True

    if isinstance(value, tuple):
        return any(_value_contains_temp(v) for v in value)

    if isinstance(value, list):
        return any(_value_contains_temp(v) for v in value)

    return False


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _max_temp_index(instructions):
    max_index = 0

    def scan(value):
        nonlocal max_index

        if _is_temp(value):
            max_index = max(max_index, int(value[1:]))

        elif isinstance(value, tuple):
            for item in value:
                scan(item)

        elif isinstance(value, list):
            for item in value:
                scan(item)

    for instr in instructions:
        scan(instr.arg1)
        scan(instr.arg2)
        scan(instr.result)

    return max_index


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _find_label(instructions, label, start):
    for i in range(start, len(instructions)):
        if instructions[i].op == "LABEL" and instructions[i].result == label:
            return i

    return None


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _last_goto_to_label(instructions, label, start, end):
    result = None

    for i in range(start, end):
        if instructions[i].op == "GOTO" and instructions[i].result == label:
            result = i

    return result


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _compute_iteration_count(start, bound, cmp_op, step):
    if step == 0:
        return None

    if cmp_op == "<" and step > 0:
        return max(0, bound - start)

    if cmp_op == "<=" and step > 0:
        return max(0, bound - start + 1)

    if cmp_op == ">" and step < 0:
        return max(0, start - bound)

    if cmp_op == ">=" and step < 0:
        return max(0, start - bound + 1)

    return None


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _replace_value_for_unroll(value, induction_var, induction_value, temp_map):
    if value == induction_var:
        return induction_value

    if _is_temp(value) and value in temp_map:
        return temp_map[value]

    if isinstance(value, tuple):
        return tuple(
            _replace_value_for_unroll(v, induction_var, induction_value, temp_map)
            for v in value
        )

    if isinstance(value, list):
        return [
            _replace_value_for_unroll(v, induction_var, induction_value, temp_map)
            for v in value
        ]

    return value


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _clone_instruction_for_unroll(instr, induction_var, induction_value, temp_map, temp_counter):
    def fresh_temp():
        temp_counter[0] += 1
        return f"t{temp_counter[0]}"

    new_result = instr.result

    defs = _defs(instr)

    for defined in defs:
        if _is_temp(defined):
            if defined not in temp_map:
                temp_map[defined] = fresh_temp()

    new_arg1 = _replace_value_for_unroll(instr.arg1, induction_var, induction_value, temp_map)
    new_arg2 = _replace_value_for_unroll(instr.arg2, induction_var, induction_value, temp_map)
    new_result = _replace_value_for_unroll(instr.result, induction_var, induction_value, temp_map)

    return TACInstruction(instr.op, new_arg1, new_arg2, new_result)


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def _body_is_safe_to_unroll(body, induction_var):
    """
    Unrolling conservador:
    - No desenrolla si hay control-flow interno.
    - No desenrolla si el cuerpo modifica la variable de inducción.
    """

    forbidden_ops = {
        "LABEL", "GOTO", "IF_FALSE", "IF_TRUE", "RETURN"
    }

    for instr in body:
        if instr.op in forbidden_ops:
            return False

        if induction_var in _defs(instr):
            return False

    return True


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def loop_unrolling(instructions, max_unroll=8):
    """
    Loop unrolling para for-loops simples.

    Detecta patrones TAC como:

        i = 0
        for1:
        t1 = i < 3
        ifFalse t1 goto endfor3
        cuerpo
        for_update2:
        i = i + 1
        goto for1
        endfor3:

    Y los transforma en:

        i = 0
        cuerpo con i = 0
        cuerpo con i = 1
        cuerpo con i = 2
        i = 3

    Solo aplica cuando:
    - inicio es constante entera
    - límite es constante entero
    - step es constante entero
    - cuerpo no tiene control-flow interno
    - número de iteraciones <= max_unroll
    """

    optimized = []
    i = 0
    temp_counter = [_max_temp_index(instructions)]

    while i < len(instructions):
        # Buscamos:
        # ASSIGN i = const
        # LABEL forN
        if (
            i + 4 < len(instructions)
            and instructions[i].op == "ASSIGN"
            and instructions[i + 1].op == "LABEL"
            and isinstance(instructions[i + 1].result, str)
            and instructions[i + 1].result.startswith("for")
        ):
            init_instr = instructions[i]
            label_instr = instructions[i + 1]
            cond_instr = instructions[i + 2]
            branch_instr = instructions[i + 3]

            induction_var = init_instr.result
            start_value = _as_int_constant(init_instr.arg1)
            loop_label = label_instr.result

            if start_value is None:
                optimized.append(instructions[i])
                i += 1
                continue

            if cond_instr.op not in {"<", "<=", ">", ">="}:
                optimized.append(instructions[i])
                i += 1
                continue

            if cond_instr.arg1 != induction_var:
                optimized.append(instructions[i])
                i += 1
                continue

            bound_value = _as_int_constant(cond_instr.arg2)

            if bound_value is None:
                optimized.append(instructions[i])
                i += 1
                continue

            if (
                branch_instr.op != "IF_FALSE"
                or branch_instr.arg1 != cond_instr.result
            ):
                optimized.append(instructions[i])
                i += 1
                continue

            end_label = branch_instr.result
            end_index = _find_label(instructions, end_label, i + 4)

            if end_index is None:
                optimized.append(instructions[i])
                i += 1
                continue

            back_goto_index = _last_goto_to_label(
                instructions,
                loop_label,
                i + 4,
                end_index
            )

            if back_goto_index is None:
                optimized.append(instructions[i])
                i += 1
                continue

            update_index = back_goto_index - 1

            if update_index <= i + 3:
                optimized.append(instructions[i])
                i += 1
                continue

            update_instr = instructions[update_index]

            if (
                update_instr.op not in {"+", "-"}
                or update_instr.result != induction_var
                or update_instr.arg1 != induction_var
            ):
                optimized.append(instructions[i])
                i += 1
                continue

            raw_step = _as_int_constant(update_instr.arg2)

            if raw_step is None:
                optimized.append(instructions[i])
                i += 1
                continue

            step = raw_step if update_instr.op == "+" else -raw_step

            iteration_count = _compute_iteration_count(
                start_value,
                bound_value,
                cond_instr.op,
                step
            )

            if iteration_count is None or iteration_count > max_unroll:
                optimized.append(instructions[i])
                i += 1
                continue

            # El cuerpo empieza después del IF_FALSE.
            body_start = i + 4

            body_end = update_index

            if (
                body_end - 1 >= body_start
                and instructions[body_end - 1].op == "LABEL"
                and isinstance(instructions[body_end - 1].result, str)
                and instructions[body_end - 1].result.startswith("for_update")
            ):
                body_end -= 1

            body = instructions[body_start:body_end]

            if not _body_is_safe_to_unroll(body, induction_var):
                optimized.append(instructions[i])
                i += 1
                continue

            # Emitimos init original.
            optimized.append(init_instr)

            current_value = start_value

            for _ in range(iteration_count):
                temp_map = {}

                for body_instr in body:
                    cloned = _clone_instruction_for_unroll(
                        body_instr,
                        induction_var,
                        current_value,
                        temp_map,
                        temp_counter
                    )
                    optimized.append(cloned)

                current_value += step

            # Preservamos valor final de la variable de inducción.
            optimized.append(
                TACInstruction("ASSIGN", arg1=current_value, result=induction_var)
            )

            # Saltamos todo el loop original hasta después del end label.
            i = end_index + 1
            continue

        optimized.append(instructions[i])
        i += 1

    return optimized


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def optimize_once(instructions):
    instructions = constant_and_copy_propagation(instructions)
    instructions = loop_unrolling(instructions, max_unroll=8)
    instructions = constant_and_copy_propagation(instructions)
    instructions = remove_dead_code_after_jumps(instructions)
    instructions = remove_redundant_gotos(instructions)
    instructions = remove_unused_labels(instructions)
    instructions = remove_redundant_assignments(instructions)
    instructions = remove_dead_temporaries(instructions)
    return instructions


# Ejecuta las pasadas de optimización sobre una lista de instrucciones TAC.
def optimizar_tac(instructions, passes=6):
    optimized = list(instructions)

    for _ in range(passes):
        before = [str(instr) for instr in optimized]

        optimized = optimize_once(optimized)

        after = [str(instr) for instr in optimized]

        if before == after:
            break

    return optimized


# Imprime el TAC ya optimizado.
def imprimir_tac_optimizado(instrucciones):
    for i, instr in enumerate(instrucciones):
        print(f"{i:04d}: {instr}")


# Guarda el TAC optimizado en disco.
def guardar_tac_optimizado(instrucciones, ruta="tac_optimized.ir"):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for instr in instrucciones:
            archivo.write(str(instr) + "\n")
