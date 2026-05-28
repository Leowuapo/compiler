# PENTA Compiler - documentación interna
# Utilidades de rutas: centraliza nombres de carpetas y archivos generados por cada corrida del compilador.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

"""Helpers para construir rutas de artefactos del pipeline."""

import os
import re


# Normaliza texto para usarlo como nombre seguro de archivo o carpeta.
def slugify(value):
    value = str(value or "run")
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    value = value.strip("._-")
    return value or "run"


# Elige el nombre base de una corrida usando la fuente o la carpeta de salida.
def run_name_from_source(source_path=None, output_dir=None):
    if source_path and source_path not in {"<terminal>", "<editor>", "<unknown>"}:
        base = os.path.splitext(os.path.basename(source_path))[0]
    elif output_dir:
        base = os.path.basename(os.path.abspath(output_dir))
    else:
        base = "run"
    return slugify(base)


# Construye todas las rutas de AST, IR y target code para una corrida.
def build_artifact_paths(output_dir=None, ast_base_path="ast", source_path=None):
    run_name = run_name_from_source(source_path, output_dir)

    if output_dir is None:
        base_dir = os.path.dirname(os.path.abspath(ast_base_path)) or "."
    else:
        base_dir = output_dir

    ast_dir = os.path.join(base_dir, "ast")
    ir_dir = os.path.join(base_dir, "ir")
    target_dir = os.path.join(base_dir, "target")

    for folder in (base_dir, ast_dir, ir_dir, target_dir):
        os.makedirs(folder, exist_ok=True)

    ast_base = os.path.join(ast_dir, f"ast_{run_name}")

    return {
        "ast_dot": f"{ast_base}.dot",
        "ast_png": f"{ast_base}.png",
        "ast_svg": f"{ast_base}.svg",
        "ast_modern_dot": f"{ast_base}.dot",
        "ast_modern_svg": f"{ast_base}.svg",
        "tac": os.path.join(ir_dir, f"tac_{run_name}.ir"),
        "tac_optimized": os.path.join(ir_dir, f"tac_optimized_{run_name}.ir"),
        "target_code": os.path.join(target_dir, f"target_code_{run_name}.asm"),
        "base_dir": base_dir,
        "ast_dir": ast_dir,
        "ir_dir": ir_dir,
        "target_dir": target_dir,
    }
