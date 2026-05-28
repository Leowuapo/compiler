#!/usr/bin/env python3
"""
Cross-platform dependency checker for PENTA Compiler.

This module is intentionally lightweight and safe to import from GUI.py.
It checks Python/Tkinter/CustomTkinter/Pillow/Graphviz and returns
platform-aware installation recommendations.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

MIN_PYTHON = (3, 10)


@dataclass(frozen=True)
class DependencyResult:
    ok: bool
    info: str
    required: bool = False


def _platform_key() -> str:
    system = platform.system().lower()
    if system.startswith("darwin"):
        return "macos"
    if system.startswith("windows"):
        return "windows"
    if system.startswith("linux"):
        return "linux"
    return "unknown"


def _recommendations() -> dict[str, str]:
    system = _platform_key()

    common_pip = (
        "python -m pip install --upgrade pip\n"
        "python -m pip install -r requirements.txt"
    )

    if system == "windows":
        return {
            "python": (
                "Install Python 3.10+ from python.org or Microsoft Store. "
                "During installation, enable 'Add python.exe to PATH'."
            ),
            "tkinter": "Tkinter is normally included with python.org installers on Windows. Reinstall Python if it is missing.",
            "customtkinter": common_pip,
            "pillow": common_pip,
            "graphviz": (
                "Install Graphviz from https://graphviz.org/download/ and add its bin folder to PATH.\n"
                "Typical PATH entry: C:\\Program Files\\Graphviz\\bin\n"
                "Then open a new terminal and verify: dot -V"
            ),
        }

    if system == "linux":
        return {
            "python": "Install Python 3.10+ with your package manager, e.g. sudo apt install python3 python3-venv python3-pip",
            "tkinter": "Ubuntu/Debian: sudo apt install python3-tk    Fedora: sudo dnf install python3-tkinter",
            "customtkinter": common_pip,
            "pillow": common_pip,
            "graphviz": "Ubuntu/Debian: sudo apt install graphviz    Fedora: sudo dnf install graphviz",
        }

    if system == "macos":
        return {
            "python": "Install Python 3.10+ from python.org or Homebrew: brew install python",
            "tkinter": "If using Homebrew Python: brew install python-tk. Python.org builds usually include Tkinter.",
            "customtkinter": common_pip,
            "pillow": common_pip,
            "graphviz": "brew install graphviz    Then verify: dot -V",
        }

    return {
        "python": "Install Python 3.10+.",
        "tkinter": "Install Tkinter for your Python distribution.",
        "customtkinter": common_pip,
        "pillow": common_pip,
        "graphviz": "Install Graphviz and make sure the 'dot' command is available in PATH.",
    }


def check_python() -> tuple[bool, str]:
    current = sys.version_info[:3]
    ok = current >= MIN_PYTHON
    info = f"Python {current[0]}.{current[1]}.{current[2]}"
    if not ok:
        info += f" (requires {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+)"
    return ok, info


def check_tkinter() -> tuple[bool, str]:
    try:
        import tkinter as tk  # noqa: F401
        return True, f"Tkinter {tk.TkVersion}"
    except Exception as exc:
        return False, f"Tkinter not available: {exc}"


def check_customtkinter() -> tuple[bool, str]:
    try:
        import customtkinter as ctk  # noqa: F401
        version = getattr(ctk, "__version__", "installed")
        return True, f"CustomTkinter {version}"
    except Exception as exc:
        return False, f"CustomTkinter not available: {exc}"


def check_pillow() -> tuple[bool, str]:
    try:
        from PIL import Image  # noqa: F401
        return True, f"Pillow {Image.__version__}"
    except Exception as exc:
        return False, f"Pillow not available: {exc}"


def check_graphviz() -> tuple[bool, str]:
    dot_path = shutil.which("dot")
    if not dot_path:
        return False, "Graphviz not available: command 'dot' was not found in PATH"

    try:
        result = subprocess.run(
            [dot_path, "-V"],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as exc:
        return False, f"Graphviz found at {dot_path}, but could not run 'dot -V': {exc}"

    version_output = (result.stderr or result.stdout or "").strip()
    if result.returncode == 0:
        return True, f"{version_output or 'Graphviz available'} ({dot_path})"

    return False, f"Graphviz command failed: {version_output or 'unknown error'} ({dot_path})"


def check_all():
    """
    Returns: (required_ok, results, recommendations)

    results keeps the historical shape expected by GUI.py:
        {name: (ok, info)}
    """
    checks: dict[str, tuple[Callable[[], tuple[bool, str]], bool]] = {
        "python": (check_python, True),
        "tkinter": (check_tkinter, True),
        "customtkinter": (check_customtkinter, True),
        "pillow": (check_pillow, False),
        "graphviz": (check_graphviz, False),
    }

    raw_results: dict[str, DependencyResult] = {}
    for name, (func, required) in checks.items():
        ok, info = func()
        raw_results[name] = DependencyResult(ok=ok, info=info, required=required)

    required_ok = all(result.ok for result in raw_results.values() if result.required)
    results = {name: (result.ok, result.info) for name, result in raw_results.items()}

    all_recs = _recommendations()
    recommendations = {
        name: all_recs.get(name, "Install or repair this dependency.")
        for name, result in raw_results.items()
        if not result.ok
    }

    return required_ok, results, recommendations


def print_status(resultados=None):
    if resultados is None:
        _, resultados, _ = check_all()

    print("\n" + "=" * 64)
    print("PENTA COMPILER - ENVIRONMENT CHECK")
    print("=" * 64)
    print(f"Platform : {platform.platform()}")
    print(f"Executable: {sys.executable}")
    print("-" * 64)

    for dep, (ok, info) in resultados.items():
        status = "[OK]" if ok else "[NO]"
        print(f"{status} {dep:<14} {info}")

    print("=" * 64 + "\n")


def show_gui_warning(missing_deps, recommendations):
    """Shows a GUI warning for missing optional dependencies."""
    from tkinter import messagebox

    if not missing_deps:
        return True

    mensaje = "DEPENDENCIAS FALTANTES O INCOMPLETAS\n\n"
    mensaje += "El programa puede funcionar con limitaciones dependiendo de lo que falte:\n\n"

    descriptions = {
        "python": "Python 3.10+ es requerido por el proyecto.",
        "tkinter": "Tkinter es requerido para abrir la GUI.",
        "customtkinter": "CustomTkinter es requerido para abrir la GUI moderna.",
        "pillow": "Pillow es opcional para cargar imágenes/logo.",
        "graphviz": "Graphviz/dot es necesario para generar AST como SVG/PNG.",
    }

    for dep in missing_deps:
        mensaje += f"- {dep}: {descriptions.get(dep, 'Dependencia requerida por el proyecto.')}\n"

    mensaje += "\nCómo instalar o corregir:\n\n"
    for dep in missing_deps:
        if dep in recommendations:
            mensaje += f"{dep}:\n{recommendations[dep]}\n\n"

    messagebox.showwarning("Dependencias del entorno", mensaje)
    return True


if __name__ == "__main__":
    required_ok, results, recommendations = check_all()
    print_status(results)

    missing = [name for name, (ok, _) in results.items() if not ok]
    if missing:
        print("Missing or incomplete dependencies:\n")
        for dep in missing:
            print(f"- {dep}:\n{recommendations.get(dep, 'No recommendation available.')}\n")

    if not required_ok:
        sys.exit(1)

    print("Required dependencies look OK.")
