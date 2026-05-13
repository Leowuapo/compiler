#!/usr/bin/env python3
"""
Verificador de dependencias para Parser & SDT - Team 05
"""

import subprocess
import sys


def check_tkinter():
    """Verifica que Tkinter esta instalado"""
    try:
        import tkinter as tk
        return True, f"Tkinter {tk.TkVersion}"
    except ImportError:
        return False, "Tkinter no instalado"


def check_pillow():
    """Verifica que Pillow (PIL) esta instalado"""
    try:
        from PIL import Image, ImageTk
        return True, f"Pillow {Image.__version__}"
    except ImportError:
        return False, "Pillow no instalado"


def check_graphviz():
    """Verifica que Graphviz (dot) esta instalado en el sistema"""
    try:
        result = subprocess.run(['dot', '-V'], capture_output=True, text=True)
        if result.returncode == 0:
            version_output = result.stderr or result.stdout
            # Extraer version (ej: 'dot - graphviz version 2.49.3')
            version = version_output.split('version')[1].strip() if 'version' in version_output else 'desconocida'
            return True, f"Graphviz {version}"
        return False, "Graphviz no instalado"
    except FileNotFoundError:
        return False, "Graphviz no instalado (comando 'dot' no encontrado)"


def check_all():
    """
    Verifica todas las dependencias
    Retorna: (obligatorias_ok, dict_resultados, dict_recomendaciones)
    """
    resultados = {
        'tkinter': check_tkinter(),
        'pillow': check_pillow(),
        'graphviz': check_graphviz()
    }
    
    # Dependencias obligatorias
    obligatorias = ['tkinter']
    obligatorias_ok = all(resultados[dep][0] for dep in obligatorias)
    
    # Recomendaciones de instalacion
    recomendaciones = {}
    
    if not resultados['pillow'][0]:
        recomendaciones['pillow'] = "  brew install pillow  o  pip install Pillow"
    
    if not resultados['graphviz'][0]:
        recomendaciones['graphviz'] = "  brew install graphviz"
    
    return obligatorias_ok, resultados, recomendaciones


def print_status(resultados):
    """Imprime el estado de las dependencias en consola"""
    print("\n" + "="*50)
    print("DEPENDENCIAS - Parser & SDT")
    print("="*50)
    
    for dep, (ok, info) in resultados.items():
        status = "[OK]" if ok else "[NO]"
        print(f"{status} {dep.capitalize()}: {info}")
    
    print("="*50 + "\n")


def show_gui_warning(missing_deps, recommendations):
    """
    Muestra una ventana de advertencia si faltan dependencias
    (para ser llamada desde la GUI)
    """
    import tkinter as tk
    from tkinter import messagebox
    
    if not missing_deps:
        return True
    
    mensaje = "DEPENDENCIAS OPCIONALES FALTANTES\n\n"
    mensaje += "El programa funcionara, pero con limitaciones:\n\n"
    
    for dep in missing_deps:
        if dep == 'pillow':
            mensaje += "- Pillow: No se podran mostrar imagenes del AST\n"
        elif dep == 'graphviz':
            mensaje += "- Graphviz: El AST no se generara como imagen (solo como .dot)\n"
    
    mensaje += "\nPara instalar las dependencias faltantes:\n\n"
    
    for dep, cmd in recommendations.items():
        mensaje += f"{dep.capitalize()}:\n{cmd}\n\n"
    
    respuesta = messagebox.askokcancel(
        "Dependencias opcionales faltantes",
        mensaje,
        icon='warning'
    )
    
    return True


if __name__ == "__main__":
    # Prueba independiente
    obligatorias_ok, resultados, recomendaciones = check_all()
    print_status(resultados)
    
    if not obligatorias_ok:
        print("ERROR: Faltan dependencias obligatorias.")
        print("Instale Tkinter con: brew install python-tk")
        sys.exit(1)
    else:
        print("Todas las dependencias obligatorias estan instaladas.")
        
        if not resultados['pillow'][0] or not resultados['graphviz'][0]:
            print("\nFaltan dependencias opcionales:")
            for dep, cmd in recomendaciones.items():
                print(f"  - {dep}: {cmd}")
        else:
            print("\nTodas las dependencias (incluyendo opcionales) estan instaladas.")