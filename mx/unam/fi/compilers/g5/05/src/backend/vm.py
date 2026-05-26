import ast


class VMError(Exception):
    pass


class VirtualMachine:
    def __init__(self, instructions):
        self.instructions = instructions
        self.functions = {}
        self.function_ends = {}
        self.params = {}
        self.labels = {}
        self.output = []

        self._index_program()

    def _index_program(self):
        current_function = None

        for index, instr in enumerate(self.instructions):
            if instr.op == "FUNC":
                current_function = instr.args[0]
                self.functions[current_function] = index
                self.params[current_function] = []

            elif instr.op == "END_FUNC":
                if current_function is not None:
                    self.function_ends[current_function] = index
                current_function = None

            elif instr.op == "PARAM" and current_function is not None:
                self.params[current_function].append(instr.args[0])

            elif instr.op == "LABEL" and current_function is not None:
                self.labels[(current_function, instr.args[0])] = index

    def run(self, entry_point="main"):
        if entry_point not in self.functions:
            raise VMError(f"entry point '{entry_point}' not found")

        result = self._run_function(entry_point, [])

        return {
            "return_value": result,
            "output": self.output,
        }

    def _new_frame(self):
        return {
            "locals": {},
            "arrays": {},
            "matrices": {},
        }

    def _run_function(self, function_name, args):
        if function_name not in self.functions:
            raise VMError(f"function '{function_name}' not found")

        expected_params = self.params.get(function_name, [])

        if len(args) != len(expected_params):
            raise VMError(
                f"function '{function_name}' expects {len(expected_params)} argument(s), got {len(args)}"
            )

        frame = self._new_frame()

        for name, value in zip(expected_params, args):
            frame["locals"][name] = value

        pc = self.functions[function_name] + 1
        end_pc = self.function_ends[function_name]
        pending_args = []

        while pc < end_pc:
            instr = self.instructions[pc]
            op = instr.op
            args_instr = instr.args

            if op in {"PARAM", "LABEL"}:
                pc += 1
                continue

            if op == "MOV":
                dest, src = args_instr
                frame["locals"][dest] = self._eval(src, frame)
                pc += 1
                continue

            if op in {
                "ADD", "SUB", "MUL", "DIV", "MOD",
                "EQ", "NE", "LT", "GT", "LE", "GE",
                "AND", "OR"
            }:
                dest, left, right = args_instr
                frame["locals"][dest] = self._eval_binary(op, left, right, frame)
                pc += 1
                continue

            if op in {"NEG", "POS", "NOT"}:
                dest, value = args_instr
                frame["locals"][dest] = self._eval_unary(op, value, frame)
                pc += 1
                continue

            if op == "JMP":
                label = args_instr[0]
                pc = self._jump_to(function_name, label)
                continue

            if op == "JZ":
                value, label = args_instr
                if not self._truthy(self._eval(value, frame)):
                    pc = self._jump_to(function_name, label)
                else:
                    pc += 1
                continue

            if op == "JNZ":
                value, label = args_instr
                if self._truthy(self._eval(value, frame)):
                    pc = self._jump_to(function_name, label)
                else:
                    pc += 1
                continue

            if op == "ARG":
                pending_args.append(self._eval(args_instr[0], frame))
                pc += 1
                continue

            if op == "CALL":
                if len(args_instr) == 3:
                    dest, called_function, n_args = args_instr
                else:
                    dest = None
                    called_function, n_args = args_instr

                n_args = int(n_args)

                if n_args == 0:
                    call_args = []
                else:
                    call_args = pending_args[-n_args:]
                    pending_args = pending_args[:-n_args]

                result = self._run_function(called_function, call_args)

                if dest is not None:
                    frame["locals"][dest] = result

                pc += 1
                continue

            if op == "RET":
                if not args_instr:
                    return None

                return self._eval(args_instr[0], frame)

            if op == "PRINT":
                value = self._eval(args_instr[0], frame)
                self.output.append(str(value))
                pc += 1
                continue

            if op == "PRINTF":
                fmt = self._eval(args_instr[0], frame)
                values = [self._eval(arg, frame) for arg in args_instr[1:]]
                self.output.append(self._format_printf(fmt, values))
                pc += 1
                continue

            if op == "STORE_ARRAY":
                name, index, value = args_instr
                index = self._as_index(self._eval(index, frame))
                value = self._eval(value, frame)

                if name not in frame["arrays"]:
                    frame["arrays"][name] = {}

                frame["arrays"][name][index] = value
                pc += 1
                continue

            if op == "LOAD_ARRAY":
                dest, name, index = args_instr
                index = self._as_index(self._eval(index, frame))

                if name not in frame["arrays"] or index not in frame["arrays"][name]:
                    raise VMError(f"array element '{name}[{index}]' has no runtime value")

                frame["locals"][dest] = frame["arrays"][name][index]
                pc += 1
                continue

            if op == "STORE_MATRIX":
                name, row, col, value = args_instr
                row = self._as_index(self._eval(row, frame))
                col = self._as_index(self._eval(col, frame))
                value = self._eval(value, frame)

                if name not in frame["matrices"]:
                    frame["matrices"][name] = {}

                frame["matrices"][name][(row, col)] = value
                pc += 1
                continue

            if op == "LOAD_MATRIX":
                dest, name, row, col = args_instr
                row = self._as_index(self._eval(row, frame))
                col = self._as_index(self._eval(col, frame))

                if name not in frame["matrices"] or (row, col) not in frame["matrices"][name]:
                    raise VMError(f"matrix element '{name}[{row}][{col}]' has no runtime value")

                frame["locals"][dest] = frame["matrices"][name][(row, col)]
                pc += 1
                continue

            raise VMError(f"unsupported target instruction: {instr}")

        return None

    def _jump_to(self, function_name, label):
        key = (function_name, label)

        if key not in self.labels:
            raise VMError(f"label '{label}' not found in function '{function_name}'")

        return self.labels[key]

    def _eval(self, value, frame):
        if value is None:
            return None

        if isinstance(value, (int, float, bool)):
            return value

        if value == "true":
            return True

        if value == "false":
            return False

        if isinstance(value, str):
            if self._is_quoted_literal(value):
                return ast.literal_eval(value)

            if value in frame["locals"]:
                return frame["locals"][value]

            raise VMError(f"variable or temporary '{value}' has no runtime value")

        return value

    def _is_quoted_literal(self, value):
        return (
            isinstance(value, str)
            and len(value) >= 2
            and (
                (value[0] == "'" and value[-1] == "'")
                or (value[0] == '"' and value[-1] == '"')
            )
        )

    def _numeric(self, value):
        if isinstance(value, bool):
            return 1 if value else 0

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return value

        if isinstance(value, str) and len(value) == 1:
            return ord(value)

        raise VMError(f"value '{value}' is not numeric")

    def _truthy(self, value):
        if isinstance(value, str) and len(value) == 1:
            return ord(value) != 0

        return bool(value)

    def _as_index(self, value):
        value = self._numeric(value)

        if not isinstance(value, int):
            raise VMError(f"index '{value}' is not an integer")

        return value

    def _eval_binary(self, op, left, right, frame):
        a = self._eval(left, frame)
        b = self._eval(right, frame)

        if op == "ADD":
            return self._numeric(a) + self._numeric(b)

        if op == "SUB":
            return self._numeric(a) - self._numeric(b)

        if op == "MUL":
            return self._numeric(a) * self._numeric(b)

        if op == "DIV":
            b_num = self._numeric(b)

            if b_num == 0:
                raise VMError("division by zero")

            a_num = self._numeric(a)

            if isinstance(a_num, int) and isinstance(b_num, int):
                return int(a_num / b_num)

            return a_num / b_num

        if op == "MOD":
            b_num = self._numeric(b)

            if b_num == 0:
                raise VMError("modulo by zero")

            return int(self._numeric(a) % b_num)

        if op == "EQ":
            return self._compare_value(a) == self._compare_value(b)

        if op == "NE":
            return self._compare_value(a) != self._compare_value(b)

        if op == "LT":
            return self._numeric(a) < self._numeric(b)

        if op == "GT":
            return self._numeric(a) > self._numeric(b)

        if op == "LE":
            return self._numeric(a) <= self._numeric(b)

        if op == "GE":
            return self._numeric(a) >= self._numeric(b)

        if op == "AND":
            return self._truthy(a) and self._truthy(b)

        if op == "OR":
            return self._truthy(a) or self._truthy(b)

        raise VMError(f"unsupported binary op '{op}'")

    def _eval_unary(self, op, value, frame):
        value = self._eval(value, frame)

        if op == "NEG":
            return -self._numeric(value)

        if op == "POS":
            return +self._numeric(value)

        if op == "NOT":
            return not self._truthy(value)

        raise VMError(f"unsupported unary op '{op}'")

    def _compare_value(self, value):
        if isinstance(value, str) and len(value) == 1:
            return ord(value)

        return value

    def _format_printf(self, fmt, values):
        result = []
        arg_index = 0
        i = 0

        while i < len(fmt):
            if fmt[i] != "%":
                result.append(fmt[i])
                i += 1
                continue

            if i + 1 >= len(fmt):
                raise VMError("incomplete printf format")

            spec = fmt[i + 1]

            if spec == "%":
                result.append("%")
                i += 2
                continue

            if arg_index >= len(values):
                raise VMError("not enough values for printf")

            value = values[arg_index]
            arg_index += 1

            if spec in {"d", "i", "u"}:
                result.append(str(int(self._numeric(value))))

            elif spec == "f":
                result.append(str(float(self._numeric(value))))

            elif spec == "c":
                if isinstance(value, str):
                    result.append(value[0])
                else:
                    result.append(chr(int(self._numeric(value))))

            elif spec == "s":
                result.append(str(value))

            elif spec == "b":
                result.append("true" if self._truthy(value) else "false")

            else:
                raise VMError(f"unsupported printf format '%{spec}'")

            i += 2

        if arg_index != len(values):
            raise VMError("too many values for printf")

        return "".join(result)


def ejecutar_target_code(instructions, entry_point="main", mostrar_salida=True):
    vm = VirtualMachine(instructions)
    resultado = vm.run(entry_point)

    if mostrar_salida:
        print("VM Output:")

        if resultado["output"]:
            for line in resultado["output"]:
                print(line)
        else:
            print("(no output)")

        print(f"VM Return Value: {resultado['return_value']}")

    return resultado