"""Puertos: lo que la aplicación necesita del mundo exterior."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from dian_hojas.dominio.modelos import (
    Cliente,
    ListadoDian,
    Periodo,
    ResultadoMes,
)


class LectorListado(Protocol):
    """Lee el listado de documentos electrónicos descargado de la DIAN."""

    def leer(self, ruta: Path) -> ListadoDian: ...


class EscritorHoja(Protocol):
    """Escribe el archivo Excel con las pestañas de trabajo."""

    def escribir(
        self,
        resultado: ResultadoMes,
        cliente: Cliente,
        periodo: Periodo,
        destino: Path,
        *,
        ruta_listado: Path,
    ) -> Path: ...
