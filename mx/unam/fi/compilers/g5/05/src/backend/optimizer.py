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

def _is_temp(value):
    return isinstance(value, str) and value.startswith("t") and value[1:].isdigit()


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


def _is_bool_text(value):
    return value in {"true", "false"}


def _is_variable_name(value):
    if not isinstance(value, str):
        return False

    if _is_quoted_literal(value):
        return False

    if _is_bool_text(value):
        return False

    return True


def _parse_literal(value):
    if isinstance(value, (int, float, bool)):
        return value

    if value == "true":
        return True

    if value == "false":
        return False

    return value


def _is_constant(value):
    parsed = _parse_literal(value)

    if isinstance(parsed, (int, float, bool)):
        return True

    if _is_quoted_literal(parsed):
        return True

    return False


def _is_numeric_or_bool_constant(value):
    parsed = _parse_literal(value)
    return isinstance(parsed, (int, float, bool))


def _is_truthy_constant(value):
    parsed = _parse_literal(value)

    if isinstance(parsed, (int, float, bool)):
        return bool(parsed)

    return None


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

def _add_use(uses, value):
    if _is_variable_name(value):
        uses.add(value)


def _add_uses_from_tuple(uses, value_tuple):
    if not isinstance(value_tuple, tuple):
        return

    for item in value_tuple:
        _add_use(uses, item)


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


def remove_redundant_assignments(instructions):
    optimized = []

    for instr in instructions:
        if instr.op == "ASSIGN" and instr.result == instr.arg1:
            continue

        optimized.append(instr)

    return optimized


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

def optimize_once(instructions):
    instructions = constant_and_copy_propagation(instructions)
    instructions = remove_dead_code_after_jumps(instructions)
    instructions = remove_redundant_gotos(instructions)
    instructions = remove_unused_labels(instructions)
    instructions = remove_redundant_assignments(instructions)
    instructions = remove_dead_temporaries(instructions)
    return instructions


def optimizar_tac(instructions, passes=6):
    optimized = list(instructions)

    for _ in range(passes):
        before = [str(instr) for instr in optimized]

        optimized = optimize_once(optimized)

        after = [str(instr) for instr in optimized]

        if before == after:
            break

    return optimized


def imprimir_tac_optimizado(instrucciones):
    for i, instr in enumerate(instrucciones):
        print(f"{i:04d}: {instr}")


def guardar_tac_optimizado(instrucciones, ruta="tac_optimized.ir"):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for instr in instrucciones:
            archivo.write(str(instr) + "\n")