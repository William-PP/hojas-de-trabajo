"""Resolución de las carpetas de trabajo, tanto en el repositorio como en el ejecutable.

- `reglas/`: tablas tributarias editables por el usuario. Se puede cambiar con la variable de
  entorno `DIAN_HOJAS_REGLAS`.
- Datos locales (SQLite de perfiles y decisiones): `~/.dian_hojas`, cambiable con
  `DIAN_HOJAS_DATOS`.

En un ejecutable de PyInstaller `reglas/` vive **al lado del `.exe`**, para que el usuario pueda
editarla. No se empaqueta dentro del binario temporal (se perdería cada vez que se abre).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

VARIABLE_REGLAS = "DIAN_HOJAS_REGLAS"
VARIABLE_DATOS = "DIAN_HOJAS_DATOS"


def directorio_reglas() -> Path:
    """Carpeta de los YAML tributarios por año."""
    valor = os.environ.get(VARIABLE_REGLAS)
    if valor:
        return Path(valor).expanduser()

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "reglas"

    # `src/dian_hojas/rutas.py` → parents[2] es la raíz del repositorio.
    return Path(__file__).resolve().parents[2] / "reglas"


def directorio_datos() -> Path:
    """Carpeta de datos locales del usuario (SQLite)."""
    valor = os.environ.get(VARIABLE_DATOS)
    if valor:
        return Path(valor).expanduser()
    return Path.home() / ".dian_hojas"
