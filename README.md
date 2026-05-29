# PENTA Compiler

-- Compilador desarrollado por el **Equipo 5** — Facultad de Ingeniería, UNAM. --


## Tabla de contenidos

- [Descripción general](#descripción-general)
- [Arquitectura del compilador](#arquitectura-del-compilador)
- [Requisitos del sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Uso](#uso)
  - [Interfaz gráfica (GUI)](#interfaz-gráfica-gui)
  - [Línea de comandos (CLI)](#línea-de-comandos-cli)
  - [Modo interactivo](#modo-interactivo)
- [Artefactos generados](#artefactos-generados)
- [Pruebas incluidas](#pruebas-incluidas)
- [Verificación del entorno](#verificación-del-entorno)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Licencia](#licencia)

## Descripción general

PENTA Compiler es un compilador completo para un subconjunto del lenguaje C que abarca todas las fases clásicas de compilación: análisis léxico, análisis sintáctico, análisis semántico con traducción dirigida por sintaxis (SDT), generación de código intermedio (TAC), optimización y generación de código objetivo. Adicionalmente, incluye una máquina virtual para ejecutar el código generado.

El proyecto cuenta tanto con una interfaz gráfica moderna (GUI) como con una interfaz de línea de comandos (CLI), lo que permite su uso en entornos de desarrollo y de demostración.

## Arquitectura del compilador

```
Código fuente (.c)
        │
        ▼
┌───────────────┐
│  Lexer        │  lector.py / lexertable.py
│  (Análisis    │  → Produce lista de tokens con línea y columna
│   léxico)     │
└──────┬────────┘
       │ tokens
       ▼
┌───────────────┐
│  Parser +     │  syntax_parser.py / sdt.py
│  SDT          │  → Construye el AST y valida semántica
│  (Sintáctico  │     (tipos, ámbitos, funciones, flujo de control)
│   + Semántico)│
└──────┬────────┘
       │ AST
       ▼
┌───────────────┐
│  Generación   │  tac.py
│  de TAC       │  → Código intermedio de tres direcciones
└──────┬────────┘
       │ TAC
       ▼
┌───────────────┐
│  Optimización │  optimizer.py
│  de TAC       │  → Propagación de constantes/copias,
│               │     simplificación algebraica,
│               │     eliminación de temporales muertos
└──────┬────────┘
       │ TAC optimizado
       ▼
┌───────────────┐
│  Código       │  target_code.py
│  objetivo     │  → Ensamblador / representación final
└──────┬────────┘
       │
       ▼
┌───────────────┐
│  Máquina      │  vm.py
│  Virtual      │  → Ejecución del código generado
└───────────────┘
```

## Requisitos del sistema

| Componente     | Versión mínima | Notas |
|----------------|----------------|-------|
| Python         | 3.10           | Requerido |
| Tkinter        | Incluido con Python | Requerido para GUI |
| CustomTkinter  | ≥ 5.2.2        | Requerido para GUI |
| Pillow         | ≥ 10.0.0       | Opcional — carga de imágenes y logos |
| Graphviz (`dot`) | Cualquiera   | Opcional — visualización del AST como SVG/PNG |

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/<org>/compiler.git
cd compiler
```

### 2. Instalar dependencias de Python

```bash
pip install -r mx/unam/fi/compilers/g5/05/requirements.txt
```

### 3. Instalar Graphviz (opcional, para visualización del AST)

**Linux (Debian/Ubuntu):**
```bash
sudo apt install graphviz
```

**macOS:**
```bash
brew install graphviz
```

**Windows:**
Descarga el instalador desde [graphviz.org/download](https://graphviz.org/download/) y agrega la carpeta `bin` al PATH del sistema (normalmente `C:\Program Files\Graphviz\bin`).

### 4. Verificar el entorno

```bash
python mx/unam/fi/compilers/g5/05/tools/check_environment.py
```

Este comando valida Python, Tkinter, CustomTkinter, Pillow y Graphviz, y ejecuta un smoke test de compilación automático.

## Uso

Todos los comandos deben ejecutarse desde la **raíz del repositorio**.

### Interfaz gráfica (GUI)

**Linux / macOS:**
```bash
bash mx/unam/fi/compilers/g5/05/scripts/run_gui.sh
```

**Windows (PowerShell):**
```powershell
.\mx\unam\fi\compilers\g5\05\scripts\run_gui.ps1
```

### Línea de comandos (CLI)

**Linux / macOS:**
```bash
# Compilar un archivo fuente
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh ruta/al/archivo.c

# Compilar con salida verbose (imprime AST, TAC y código objetivo en consola)
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh ruta/al/archivo.c --verbose

# Especificar directorio de salida
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh ruta/al/archivo.c -o salida/

# Ingresar código directamente desde la terminal
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh --terminal
```

**Windows (PowerShell):**
```powershell
.\mx\unam\fi\compilers\g5\05\scripts\run_cli.ps1 ruta\al\archivo.c
.\mx\unam\fi\compilers\g5\05\scripts\run_cli.ps1 ruta\al\archivo.c --verbose
```

#### Opciones disponibles

| Argumento            | Descripción |
|----------------------|-------------|
| `source`             | Ruta al archivo fuente `.c` (opcional; sin él, activa el modo interactivo) |
| `-o`, `--output-dir` | Directorio donde se guardarán los artefactos generados |
| `-v`, `--verbose`    | Imprime en consola el AST, TAC, TAC optimizado y código objetivo |
| `--terminal`         | Lee el código fuente directamente desde la entrada de la terminal |

### Modo interactivo

Si se ejecuta sin argumentos, el compilador solicita elegir entre cargar un archivo o ingresar código directamente:

```
Select how you will enter your code (archive/terminal):
```

## Artefactos generados

Cada compilación genera una carpeta en `src/outputs/<nombre_archivo>/` con los siguientes artefactos:

```
outputs/
└── mi_programa/
    ├── ast/
    │   └── ast_mi_programa.dot        # Árbol sintáctico abstracto (formato Graphviz)
    ├── ir/
    │   ├── tac_mi_programa.ir         # Código intermedio TAC
    │   └── tac_optimized_mi_programa.ir  # TAC después de optimizaciones
    └── target/
        └── target_code_mi_programa.asm   # Código objetivo generado
```

## Pruebas incluidas

El directorio `src/tests/` contiene casos de prueba organizados por categoría:

| Categoría                   | Descripción |
|-----------------------------|-------------|
| `valid/`                    | Programas correctos que deben compilar exitosamente |
| `lexical_errors/`           | Errores como símbolos inválidos o cadenas sin cerrar |
| `syntax_errors/`            | Errores como punto y coma faltante o uso de `do-while` (no soportado) |
| `semantic_errors/`          | Errores de tipo, uso antes de inicialización, retorno incorrecto, etc. |
| `runtime_errors_optional/`  | Casos opcionales de errores en tiempo de ejecución |

**Ejemplo de prueba válida:**
```bash
bash mx/unam/fi/compilers/g5/05/scripts/run_cli.sh \
  mx/unam/fi/compilers/g5/05/src/tests/valid/01_full_feature_success.c --verbose
```

## Verificación del entorno

```bash
# Verificación completa (dependencias + smoke test)
python mx/unam/fi/compilers/g5/05/tools/check_environment.py

# Solo smoke test
python mx/unam/fi/compilers/g5/05/tools/check_environment.py --smoke-only

# Solo dependencias
python mx/unam/fi/compilers/g5/05/tools/check_environment.py --no-smoke
```

## Estructura del repositorio

```
compiler/
├── README.md
├── LICENSE
├── .gitignore
└── mx/unam/fi/compilers/g5/05/
    ├── requirements.txt
    ├── scripts/
    │   ├── run_cli.sh          # Arranque CLI en Linux/macOS
    │   ├── run_cli.ps1         # Arranque CLI en Windows
    │   ├── run_gui.sh          # Arranque GUI en Linux/macOS
    │   └── run_gui.ps1         # Arranque GUI en Windows
    ├── tools/
    │   └── check_environment.py  # Validador de entorno y smoke test
    ├── doc/
    │   └── 05-Compilers-Parser.pdf  # Documentación técnica del parser
    └── src/
        ├── main.py             # Punto de entrada CLI
        ├── GUI.py              # Interfaz gráfica
        ├── deps_checker.py     # Verificador de dependencias
        ├── lexer/
        │   ├── lector.py       # Tokenizador
        │   └── lexertable.py   # Tabla de patrones léxicos
        ├── parser_sdt/
        │   ├── syntax_parser.py  # Parser sintáctico
        │   ├── sdt.py            # Traducción dirigida por sintaxis
        │   ├── parsertable.py    # Tabla de parsing
        │   ├── pipeline/         # Artefactos y reportes del pipeline
        │   └── semantic/         # AST, tabla de símbolos, tipos, errores
        ├── backend/
        │   ├── tac.py            # Generación de TAC
        │   ├── optimizer.py      # Optimización de TAC
        │   ├── target_code.py    # Generación de código objetivo
        │   └── vm.py             # Máquina virtual
        ├── assets/
        │   └── grammar/          # Visualizador HTML de la gramática
        └── tests/
            ├── valid/
            ├── lexical_errors/
            ├── syntax_errors/
            ├── semantic_errors/
            └── runtime_errors_optional/
```

## Licencia

Este proyecto está disponible bajo los términos descritos en el archivo [LICENSE](LICENSE).

---

*Equipo 5 — Compiladores, Facultad de Ingeniería, UNAM*
