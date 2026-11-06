"""Pruebas mínimas de la Fase 0: el paquete existe y respeta la regla de dependencias."""

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_version_del_paquete():
    import dian_hojas

    assert dian_hojas.__version__ == "0.1.0"


def test_dominio_es_python_puro():
    """El dominio y las reglas no deben arrastrar pandas, openpyxl ni PySide6."""
    codigo = (
        "import sys;"
        "import dian_hojas.dominio, dian_hojas.reglas;"
        "prohibidos = {'pandas', 'openpyxl', 'PySide6', 'sqlite3'} & set(sys.modules);"
        "assert not prohibidos, prohibidos"
    )
    entorno = dict(os.environ, PYTHONPATH=str(RAIZ / "src"))
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        capture_output=True,
        text=True,
        env=entorno,
    )
    assert resultado.returncode == 0, resultado.stderr
