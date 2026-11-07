"""Punto de entrada ejecutable: `python -m dian_hojas` y el `.exe` de PyInstaller."""

from __future__ import annotations

from dian_hojas.interfaz.main import run

if __name__ == "__main__":
    raise SystemExit(run())
