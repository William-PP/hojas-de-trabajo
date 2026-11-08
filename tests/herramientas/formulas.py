"""Evaluador mínimo de las fórmulas que escribe la aplicación.

Sirve para comprobar en las pruebas que los totales dan lo que deben sin depender de que Excel o
LibreOffice recalculen el archivo. Solo entiende lo que el escritor genera: `=SUM(rango)`,
`=Xfila-Yfila` y `=Xfila`. Cualquier otra fórmula falla ruidosamente.
"""

from __future__ import annotations

import re
from typing import Any

from openpyxl.utils import column_index_from_string, get_column_letter

_SUM = re.compile(r"^=SUM\(([A-Z]{1,2})(\d+):([A-Z]{1,2})(\d+)\)$")
_RESTA = re.compile(r"^=([A-Z]{1,2})(\d+)-([A-Z]{1,2})(\d+)$")
_RESTA_DOS = re.compile(r"^=([A-Z]{1,2})(\d+)-([A-Z]{1,2})(\d+)-([A-Z]{1,2})(\d+)$")
_CELDA = re.compile(r"^=([A-Z]{1,2})(\d+)$")


def _celda(ws, letra: str, fila: int) -> Any:
    return ws.cell(row=fila, column=column_index_from_string(letra)).value


def valor(ws, referencia: str, _vistos: tuple[str, ...] = ()) -> Any:
    """Valor de la celda, resolviendo las fórmulas soportadas."""
    if referencia in _vistos:
        raise ValueError(f"referencia circular en {referencia}")
    bruto = ws[referencia].value
    if not isinstance(bruto, str) or not bruto.startswith("="):
        return bruto
    return _evaluar(ws, bruto, _vistos + (referencia,))


def _evaluar(ws, formula: str, vistos: tuple[str, ...]) -> float:
    if (encontrado := _SUM.match(formula)) is not None:
        col_ini, fila_ini, col_fin, fila_fin = encontrado.groups()
        if column_index_from_string(col_ini) != column_index_from_string(col_fin):
            raise ValueError(f"SUM entre columnas distintas: {formula!r}")
        total = 0.0
        for fila in range(int(fila_ini), int(fila_fin) + 1):
            sumando = valor(ws, f"{col_ini}{fila}", vistos)
            total += float(sumando or 0)
        return total

    if (encontrado := _RESTA_DOS.match(formula)) is not None:
        col_a, fila_a, col_b, fila_b, col_c, fila_c = encontrado.groups()
        return (
            float(valor(ws, f"{col_a}{fila_a}", vistos) or 0)
            - float(valor(ws, f"{col_b}{fila_b}", vistos) or 0)
            - float(valor(ws, f"{col_c}{fila_c}", vistos) or 0)
        )

    if (encontrado := _RESTA.match(formula)) is not None:
        col_a, fila_a, col_b, fila_b = encontrado.groups()
        return float(valor(ws, f"{col_a}{fila_a}", vistos) or 0) - float(
            valor(ws, f"{col_b}{fila_b}", vistos) or 0
        )

    if (encontrado := _CELDA.match(formula)) is not None:
        letra, fila = encontrado.groups()
        return float(valor(ws, f"{letra}{fila}", vistos) or 0)

    raise ValueError(f"fórmula no soportada por el evaluador de pruebas: {formula!r}")


def fila_numerica(ws, fila: int, columnas=("P", "Q", "R")) -> dict[str, float]:
    return {letra: float(valor(ws, f"{letra}{fila}") or 0) for letra in columnas}
