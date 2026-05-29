# PENTA Compiler

> A C-subset compiler developed by **Team 5** for the Compilers course — Faculty of Engineering, UNAM.

---

## Table of Contents

- [Overview](#overview)
- [Compiler Architecture](#compiler-architecture)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Graphical Interface (GUI)](#graphical-interface-gui)
  - [Command Line (CLI)](#command-line-cli)
  - [Interactive Mode](#interactive-mode)
- [Generated Artifacts](#generated-artifacts)
- [Included Tests](#included-tests)
- [Environment Check](#environment-check)
- [Repository Structure](#repository-structure)
- [License](#license)

---

## Overview

PENTA Compiler is a full compiler for a subset of the C language covering all classic compilation phases: lexical analysis, syntactic analysis, semantic analysis with syntax-directed translation (SDT), intermediate code generation (TAC), optimization, and target code generation. It also includes a virtual machine to execute the generated code.

The project provides both a modern graphical interface (GUI) and a command-line interface (CLI), making it suitable for development and demonstration environments.

---

## Compiler Architecture

```
Source code (.c)
        │
        ▼
┌───────────────┐
│  Lexer        │  lector.py / lexertable.py
│               │  → Produces a token list with line and column info
└──────┬────────┘
       │ tokens
       ▼
┌───────────────┐
│  Parser +     │  syntax_parser.py / sdt.py
│  SDT          │  → Builds the AST and validates semantics
│               │     (types, scopes, functions, control flow)
└──────┬────────┘
       │ AST
       ▼
┌───────────────┐
│  TAC          │  tac.py
│  Generation   │  → Three-address intermediate code
└──────┬────────┘
       │ TAC
       ▼
┌───────────────┐
│  TAC          │  optimizer.py
│  Optimizer    │  → Constant/copy propagation,
│               │     algebraic simplification,
│               │     dead temporary elimination
└──────┬────────┘
       │ Optimized TAC
       ▼
┌───────────────┐
│  Target Code  │  target_code.py
│  Generation   │  → Assembly / final representation
└──────┬────────┘
       │
       ▼
┌───────────────┐
│  Virtual      │  vm.py
│  Machine      │  → Executes the generated code
└───────────────┘
```

---

## System Requirements

| Component       | Minimum Version     | Notes |
|-----------------|---------------------|-------|
| Python          | 3.10                | Required |
| Tkinter         | Bundled with Python | Required for GUI |
| CustomTkinter   | ≥ 5.2.2             | Required for GUI |
| Pillow          | ≥ 10.0.0            | Optional — image and logo loading |
| Graphviz (`dot`) | Any               | Optional — AST visualization as SVG/PNG |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<org>/compiler.git
cd compiler
```

### 2. Install Python dependencies

```bash
pip install -r mx/unam/fi/compilers/g5/05/requirements.txt
```

### 3. Install Graphviz (optional, for AST visualization)

**Linux (Debian/Ubuntu):**
```bash
sudo apt install graphviz
```

**macOS:**
```bash
brew install graphviz
```

**Windows:**
Download the installer from [graphviz.org/download](https://graphviz.org/download/) and add the `bin` folder to the system PATH (typically `C:\Program Files\Graphviz\bin`).

### 4. Verify the environment

```bash
python mx/unam/fi/compilers/g5/05/tools/check_environment.py
```

This command checks Python, Tkinter, CustomTkinter, Pillow, and Graphviz, and runs an automatic compilation smoke test.

---

## Usage

All commands should be run from the **repository root**.

### Graphical Interface (GUI)

**Linux / macOS:**
```bash
bash mx/unam/fi/compilers/g5/05/scripts/run_gui.sh
```

**Windows (PowerShell):**
```powershell
.\mx\unam\fi\compilers\g5\05\scripts\run_gui.ps1
```

### Command Line (CLI)

**Linux / macOS:**
```bash
# Compile a source file
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh path/to/file.c

# Compile with verbose output (prints AST, TAC, and target code to console)
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh path/to/file.c --verbose

# Specify an output directory
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh path/to/file.c -o output/

# Enter code directly from the terminal
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh --terminal
```

**Windows (PowerShell):**
```powershell
.\mx\unam\fi\compilers\g5\05\scripts\run_cli.ps1 path\to\file.c
.\mx\unam\fi\compilers\g5\05\scripts\run_cli.ps1 path\to\file.c --verbose
```

#### Available options

| Argument             | Description |
|----------------------|-------------|
| `source`             | Path to the `.c` source file (optional; omitting it activates interactive mode) |
| `-o`, `--output-dir` | Directory where generated artifacts will be saved |
| `-v`, `--verbose`    | Prints AST, TAC, optimized TAC, and target code to the console |
| `--terminal`         | Reads source code directly from terminal input |

### Interactive Mode

When run without arguments, the compiler prompts you to choose between loading a file or entering code directly:

```
Select how you will enter your code (archive/terminal):
```

---

## Generated Artifacts

Each compilation produces a folder under `src/outputs/<filename>/` containing:

```
outputs/
└── my_program/
    ├── ast/
    │   └── ast_my_program.dot              # Abstract syntax tree (Graphviz format)
    ├── ir/
    │   ├── tac_my_program.ir               # TAC intermediate code
    │   └── tac_optimized_my_program.ir     # TAC after optimizations
    └── target/
        └── target_code_my_program.asm      # Generated target code
```

---

## Included Tests

The `src/tests/` directory contains test cases organized by category:

| Category                    | Description |
|-----------------------------|-------------|
| `valid/`                    | Correct programs that should compile successfully |
| `lexical_errors/`           | Errors such as invalid symbols or unclosed strings |
| `syntax_errors/`            | Errors such as missing semicolons or unsupported `do-while` |
| `semantic_errors/`          | Type errors, use-before-init, return type mismatches, etc. |
| `runtime_errors_optional/`  | Optional runtime error cases |

**Example — running a valid test:**
```bash
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh \
  mx/unam/fi/compilers/g5/05/src/tests/valid/01_full_feature_success.c --verbose
```

---

## Environment Check

```bash
# Full check (dependencies + smoke test)
python mx/unam/fi/compilers/g5/05/tools/check_environment.py

# Smoke test only
python mx/unam/fi/compilers/g5/05/tools/check_environment.py --smoke-only

# Dependencies only
python mx/unam/fi/compilers/g5/05/tools/check_environment.py --no-smoke
```

---

## Repository Structure

```
compiler/
├── README.md
├── LICENSE
├── .gitignore
└── mx/unam/fi/compilers/g5/05/
    ├── requirements.txt
    ├── scripts/
    │   ├── run_cli.sh           # CLI launcher for Linux/macOS
    │   ├── run_cli.ps1          # CLI launcher for Windows
    │   ├── run_gui.sh           # GUI launcher for Linux/macOS
    │   └── run_gui.ps1          # GUI launcher for Windows
    ├── tools/
    │   └── check_environment.py # Environment validator and smoke test
    ├── doc/
    │   └── 05-Compilers-Parser.pdf  # Parser technical documentation
    └── src/
        ├── main.py              # CLI entry point
        ├── GUI.py               # Graphical interface
        ├── deps_checker.py      # Dependency checker
        ├── lexer/
        │   ├── lector.py        # Tokenizer
        │   └── lexertable.py    # Lexical pattern table
        ├── parser_sdt/
        │   ├── syntax_parser.py # Syntactic parser
        │   ├── sdt.py           # Syntax-directed translation
        │   ├── parsertable.py   # Parsing table
        │   ├── pipeline/        # Pipeline artifacts and reports
        │   └── semantic/        # AST nodes, symbol table, types, errors
        ├── backend/
        │   ├── tac.py           # TAC generation
        │   ├── optimizer.py     # TAC optimization
        │   ├── target_code.py   # Target code generation
        │   └── vm.py            # Virtual machine
        ├── assets/
        │   └── grammar/         # HTML grammar visualizer
        └── tests/
            ├── valid/
            ├── lexical_errors/
            ├── syntax_errors/
            ├── semantic_errors/
            └── runtime_errors_optional/
```

---

## License

This project is available under the terms described in the [LICENSE](LICENSE) file.

---

*Team 5 — Compilers, Faculty of Engineering, UNAM*
