#!/usr/bin/env python3
# PENTA Compiler - documentación interna
# Validador de entorno: combina revisión de dependencias con una compilación pequeña de prueba.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

"""Cross-platform environment and smoke-test checker for PENTA Compiler.

Run from the repository root:
    python tools/check_environment.py

Optional smoke test only:
    python tools/check_environment.py --smoke-only
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


# Ejecuta la revisión de dependencias y muestra recomendaciones si algo falta.
def run_dependency_check() -> bool:
    from deps_checker import check_all, print_status

    required_ok, results, recommendations = check_all()
    print_status(results)

    missing = [name for name, (ok, _) in results.items() if not ok]
    if missing:
        print("Install/fix recommendations:\n")
        for dep in missing:
            print(f"[{dep}]\n{recommendations.get(dep, 'No recommendation available.')}\n")

    return required_ok


# Compila un programa mínimo para confirmar que las fases principales generan artefactos.
def run_smoke_test() -> bool:
    import main

    code = """int main() {
    int x = 2 + 3;
    print(x);
    return x;
}"""

    output_dir = ROOT / "outputs" / "environment_smoke_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Running CLI smoke test...")
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        ok = main.compile_terminal(
            code,
            output_dir=str(output_dir),
            verbose=False,
        )

    captured = buffer.getvalue()
    if captured.strip():
        print(captured)

    expected_files = [
        output_dir / "ast" / "ast_environment_smoke_test.dot",
        output_dir / "ir" / "tac_environment_smoke_test.ir",
        output_dir / "ir" / "tac_optimized_environment_smoke_test.ir",
        output_dir / "target" / "target_code_environment_smoke_test.asm",
    ]

    missing_files = [path for path in expected_files if not path.exists()]

    if not ok:
        print("[FAIL] Smoke test compilation failed.")
        return False

    if missing_files:
        print("[FAIL] Smoke test compiled, but expected files are missing:")
        for path in missing_files:
            print(f"  - {path}")
        return False

    print("[OK] Smoke test compiled successfully.")
    print(f"[OK] Artifacts generated under: {output_dir}")
    return True


# Encapsula una parte puntual del flujo para mantener el archivo legible y reutilizable.
def main_cli() -> int:
    parser = argparse.ArgumentParser(description="Check PENTA Compiler environment.")
    parser.add_argument("--smoke-only", action="store_true", help="Run only the compiler smoke test.")
    parser.add_argument("--no-smoke", action="store_true", help="Skip compiler smoke test.")
    args = parser.parse_args()

    os.chdir(ROOT)

    deps_ok = True
    if not args.smoke_only:
        deps_ok = run_dependency_check()

    smoke_ok = True
    if not args.no_smoke:
        smoke_ok = run_smoke_test()

    if deps_ok and smoke_ok:
        print("\nEnvironment check finished successfully.")
        return 0

    print("\nEnvironment check found issues. Review the messages above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main_cli())
