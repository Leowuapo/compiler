#!/usr/bin/env bash
# =============================================================================
# PENTA Compiler — Lanzador rápido
# Uso:
#   ./penta.sh              →  Abre la GUI
#   ./penta.sh cli          →  Modo interactivo en terminal
#   ./penta.sh cli archivo.c           →  Compila un archivo
#   ./penta.sh cli archivo.c --verbose →  Compila con salida detallada
#   ./penta.sh check        →  Verifica dependencias del entorno
#   ./penta.sh help         →  Muestra esta ayuda
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Localizar la raíz del repositorio (el directorio que contiene este script)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$SCRIPT_DIR/mx/unam/fi/compilers/g5/05"
SRC="$BASE/src"

# ---------------------------------------------------------------------------
# Verificar Python 3.10+
# ---------------------------------------------------------------------------
check_python() {
    if ! command -v python3 &>/dev/null; then
        echo "[ERROR] python3 no encontrado. Instala Python 3.10+ desde https://www.python.org"
        exit 1
    fi

    local ver
    ver=$(python3 -c "import sys; print(sys.version_info >= (3,10))")
    if [ "$ver" != "True" ]; then
        echo "[ERROR] Se requiere Python 3.10 o superior."
        python3 --version
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Instalar dependencias si faltan
# ---------------------------------------------------------------------------
install_deps() {
    echo ">>> Verificando dependencias de Python..."
    python3 -m pip install --quiet --upgrade pip
    python3 -m pip install --quiet -r "$BASE/requirements.txt"
    echo ">>> Dependencias listas."
}

# ---------------------------------------------------------------------------
# Subcomandos
# ---------------------------------------------------------------------------
cmd_gui() {
    echo ">>> Abriendo PENTA Compiler GUI..."
    cd "$SRC"
    python3 GUI.py
}

cmd_cli() {
    cd "$SRC"
    python3 main.py "$@"
}

cmd_check() {
    echo ">>> Verificando entorno PENTA Compiler..."
    cd "$BASE"
    python3 tools/check_environment.py
}

cmd_help() {
    cat <<'HELP'

PENTA Compiler — Lanzador rápido
=================================

  ./penta.sh                        Abre la interfaz gráfica (GUI)
  ./penta.sh cli                    Modo interactivo en terminal
  ./penta.sh cli <archivo.c>        Compila el archivo indicado
  ./penta.sh cli <archivo.c> -v     Compila con salida verbose
  ./penta.sh cli --terminal         Ingresa código directo en consola
  ./penta.sh check                  Verifica dependencias y smoke test
  ./penta.sh install                Instala dependencias Python
  ./penta.sh help                   Muestra esta ayuda

Opciones CLI:
  -o, --output-dir <dir>   Directorio de salida para artefactos
  -v, --verbose            Imprime AST, TAC y código objetivo en consola
  --terminal               Lee código desde stdin

Ejemplos:
  ./penta.sh cli src/tests/valid/01_full_feature_success.c --verbose
  ./penta.sh cli src/tests/lexical_errors/20_lexical_invalid_symbol.c
  ./penta.sh check --smoke-only

HELP
}

# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
check_python

COMMAND="${1:-gui}"

case "$COMMAND" in
    gui)
        install_deps
        cmd_gui
        ;;
    cli)
        shift || true
        install_deps
        cmd_cli "$@"
        ;;
    check)
        shift || true
        install_deps
        cmd_check "$@"
        ;;
    install)
        install_deps
        echo ">>> Instalación completada."
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        echo "[ERROR] Comando desconocido: '$COMMAND'"
        cmd_help
        exit 1
        ;;
esac
