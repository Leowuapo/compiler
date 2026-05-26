from .tac import TACInstruction


BIN_OPS = {
    "+", "-", "*", "/", "%",
    "==", "!=", "<", ">", "<=", ">=",
    "&&", "||"
}

UNARY_OPS = {"NEG", "POS", "!"}


def _is_int_literal(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_float_literal(value):
    return isinstance(value, float)


def _is_bool_literal(value):
    return isinstance(value, bool)


def _is_numeric_literal(value):
    return _is_int_literal(value) or _is_float_literal(value)


def _parse_literal(value):
    """
    Convierte literales TAC simples a valores Python cuando sea seguro.

    El TAC puede traer:
    - int/float reales
    - "true"/"false"
    - strings con comillas, por ejemplo "'hola'" o "'A'"
    - nombres de variables como x, t1, total
    """
    if isinstance(value, (int, float, bool)):
        return value

    if value == "true":
        return True

    if value == "false":
        return False

    return value


def _is_constant(value):
    value = _parse_literal(value)

    return isinstance(value, (int, float, bool))


def _truthy(value):
    value = _parse_literal(value)
    return bool(value)


def _eval_binary(op, arg1, arg2):
    a = _parse_literal(arg1)
    b = _parse_literal(arg2)

    if not isinstance(a, (int, float, bool)):
        return None

    if not isinstance(b, (int, float, bool)):
        return None

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
    """
    Simplificaciones locales seguras.
    No hace propagación entre instrucciones.
    """

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
        if b == 0 or a == 0:
            return TACInstruction("ASSIGN", arg1=0, result=r)

    if op == "/":
        if b == 1:
            return TACInstruction("ASSIGN", arg1=instr.arg1, result=r)

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


def constant_folding(instructions):
    optimizadas = []

    for instr in instructions:
        if instr.op in BIN_OPS:
            folded = _eval_binary(instr.op, instr.arg1, instr.arg2)

            if folded is not None:
                optimizadas.append(
                    TACInstruction("ASSIGN", arg1=folded, result=instr.result)
                )
                continue

            optimizadas.append(_simplify_algebraic(instr))
            continue

        if instr.op in UNARY_OPS:
            folded = _eval_unary(instr.op, instr.arg1)

            if folded is not None:
                optimizadas.append(
                    TACInstruction("ASSIGN", arg1=folded, result=instr.result)
                )
                continue

        optimizadas.append(instr)

    return optimizadas


def remove_dead_code_after_jumps(instructions):
    """
    Elimina instrucciones inalcanzables después de:
    - GOTO
    - RETURN

    Hasta encontrar un LABEL o END_FUNC.
    """

    optimizadas = []
    unreachable = False

    for instr in instructions:
        if instr.op in {"LABEL", "END_FUNC", "FUNC"}:
            unreachable = False
            optimizadas.append(instr)
            continue

        if unreachable:
            continue

        optimizadas.append(instr)

        if instr.op in {"GOTO", "RETURN"}:
            unreachable = True

    return optimizadas


def remove_redundant_gotos(instructions):
    """
    Elimina:
      goto L1
      L1:

    porque el flujo ya cae naturalmente a L1.
    """

    optimizadas = []

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

        optimizadas.append(instr)
        i += 1

    return optimizadas


def optimize_once(instructions):
    instructions = constant_folding(instructions)
    instructions = remove_dead_code_after_jumps(instructions)
    instructions = remove_redundant_gotos(instructions)
    return instructions


def optimizar_tac(instructions, passes=2):
    optimizadas = list(instructions)

    for _ in range(passes):
        anterior = [str(i) for i in optimizadas]
        optimizadas = optimize_once(optimizadas)
        actual = [str(i) for i in optimizadas]

        if actual == anterior:
            break

    return optimizadas


def imprimir_tac_optimizado(instrucciones):
    for i, instr in enumerate(instrucciones):
        print(f"{i:04d}: {instr}")


def guardar_tac_optimizado(instrucciones, ruta="tac_optimized.ir"):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for instr in instrucciones:
            archivo.write(str(instr) + "\n")