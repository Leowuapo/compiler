# PENTA Compiler - documentación interna
# Generación de código objetivo propio: traduce TAC a instrucciones simples que la VM puede ejecutar.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

from dataclasses import dataclass


# Representa una instrucción del código objetivo que entiende la VM.
@dataclass
class TargetInstruction:
    op: str
    args: list

    # Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
    def __str__(self):
        op = self.op
        args = self.args

        if op == "FUNC":
            return f"FUNC {args[0]}"

        if op == "END_FUNC":
            return f"END_FUNC {args[0]}"

        if op == "PARAM":
            return f"PARAM {args[0]}"

        if op == "LABEL":
            return f"{args[0]}:"

        if op == "MOV":
            return f"MOV {args[0]}, {args[1]}"

        if op in {
            "ADD", "SUB", "MUL", "DIV", "MOD",
            "EQ", "NE", "LT", "GT", "LE", "GE",
            "AND", "OR"
        }:
            return f"{op} {args[0]}, {args[1]}, {args[2]}"

        if op in {"NEG", "POS", "NOT"}:
            return f"{op} {args[0]}, {args[1]}"

        if op == "JMP":
            return f"JMP {args[0]}"

        if op == "JZ":
            return f"JZ {args[0]}, {args[1]}"

        if op == "JNZ":
            return f"JNZ {args[0]}, {args[1]}"

        if op == "ARG":
            return f"ARG {args[0]}"

        if op == "CALL":
            if len(args) == 3:
                return f"CALL {args[0]}, {args[1]}, {args[2]}"
            return f"CALL {args[0]}, {args[1]}"

        if op == "RET":
            if args:
                return f"RET {args[0]}"
            return "RET"

        if op == "PRINT":
            return f"PRINT {args[0]}"

        if op == "PRINTF":
            if len(args) > 1:
                rest = ", ".join(map(str, args[1:]))
                return f"PRINTF {args[0]}, {rest}"
            return f"PRINTF {args[0]}"

        if op == "LOAD_ARRAY":
            return f"LOAD_ARRAY {args[0]}, {args[1]}, {args[2]}"

        if op == "STORE_ARRAY":
            return f"STORE_ARRAY {args[0]}, {args[1]}, {args[2]}"

        if op == "LOAD_MATRIX":
            return f"LOAD_MATRIX {args[0]}, {args[1]}, {args[2]}, {args[3]}"

        if op == "STORE_MATRIX":
            return f"STORE_MATRIX {args[0]}, {args[1]}, {args[2]}, {args[3]}"

        return f"{op} " + ", ".join(map(str, args))


BIN_OP_MAP = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "%": "MOD",
    "==": "EQ",
    "!=": "NE",
    "<": "LT",
    ">": "GT",
    "<=": "LE",
    ">=": "GE",
    "&&": "AND",
    "||": "OR",
}

UNARY_OP_MAP = {
    "NEG": "NEG",
    "POS": "POS",
    "!": "NOT",
}


# Traduce cada instrucción TAC a una instrucción del target code.
def generar_target_code(tac_instructions):
    target = []

    for instr in tac_instructions:
        op = instr.op

        if op == "FUNC":
            target.append(TargetInstruction("FUNC", [instr.result]))

        elif op == "END_FUNC":
            target.append(TargetInstruction("END_FUNC", [instr.result]))

        elif op == "PARAM":
            target.append(TargetInstruction("PARAM", [instr.result]))

        elif op == "LABEL":
            target.append(TargetInstruction("LABEL", [instr.result]))

        elif op == "ASSIGN":
            target.append(TargetInstruction("MOV", [instr.result, instr.arg1]))

        elif op in BIN_OP_MAP:
            target.append(
                TargetInstruction(
                    BIN_OP_MAP[op],
                    [instr.result, instr.arg1, instr.arg2]
                )
            )

        elif op in UNARY_OP_MAP:
            target.append(
                TargetInstruction(
                    UNARY_OP_MAP[op],
                    [instr.result, instr.arg1]
                )
            )

        elif op == "GOTO":
            target.append(TargetInstruction("JMP", [instr.result]))

        elif op == "IF_FALSE":
            target.append(TargetInstruction("JZ", [instr.arg1, instr.result]))

        elif op == "IF_TRUE":
            target.append(TargetInstruction("JNZ", [instr.arg1, instr.result]))

        elif op == "ARG":
            target.append(TargetInstruction("ARG", [instr.result]))

        elif op == "CALL":
            if instr.result is None:
                target.append(TargetInstruction("CALL", [instr.arg1, instr.arg2]))
            else:
                target.append(TargetInstruction("CALL", [instr.result, instr.arg1, instr.arg2]))

        elif op == "RETURN":
            if instr.result is None:
                target.append(TargetInstruction("RET", []))
            else:
                target.append(TargetInstruction("RET", [instr.result]))

        elif op == "PRINT":
            target.append(TargetInstruction("PRINT", [instr.result]))

        elif op == "PRINTF":
            args = [instr.arg1] + list(instr.arg2 or [])
            target.append(TargetInstruction("PRINTF", args))

        elif op == "LOAD_ARRAY":
            target.append(
                TargetInstruction(
                    "LOAD_ARRAY",
                    [instr.result, instr.arg1, instr.arg2]
                )
            )

        elif op == "STORE_ARRAY":
            nombre, indice = instr.result
            target.append(
                TargetInstruction(
                    "STORE_ARRAY",
                    [nombre, indice, instr.arg1]
                )
            )

        elif op == "LOAD_MATRIX":
            nombre, fila, columna = instr.arg1
            target.append(
                TargetInstruction(
                    "LOAD_MATRIX",
                    [instr.result, nombre, fila, columna]
                )
            )

        elif op == "STORE_MATRIX":
            nombre, fila, columna = instr.result
            target.append(
                TargetInstruction(
                    "STORE_MATRIX",
                    [nombre, fila, columna, instr.arg1]
                )
            )

        else:
            target.append(TargetInstruction("RAW", [str(instr)]))

    return target


# Imprime el target code para revisión humana.
def imprimir_target_code(instrucciones):
    for i, instr in enumerate(instrucciones):
        print(f"{i:04d}: {instr}")


# Guarda el target code en un archivo .asm.
def guardar_target_code(instrucciones, ruta="target_code.asm"):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for instr in instrucciones:
            archivo.write(str(instr) + "\n")
