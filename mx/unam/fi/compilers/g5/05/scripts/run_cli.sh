#!/usr/bin/env bash
# PENTA Compiler - documentación interna
# Script auxiliar para abrir el proyecto desde una ruta estable.
# No modifica variables del compilador; solo ubica la raíz y ejecuta el comando correspondiente.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/src"
python3 main.py "$@"
