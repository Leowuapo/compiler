#!/usr/bin/env python3
import os
import sys

# Añadir la carpeta src al path
SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from main import main

if __name__ == "__main__":
    main()