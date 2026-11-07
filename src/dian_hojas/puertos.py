"""Puertos: lo que la aplicación necesita del mundo exterior."""

from __future__ import annotations

from pathlib import Path
from typing import Collection, Protocol

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
        retefuente: object | None = None,
        soportes_verificados: Collection[str] | None = None,
    ) -> Path: ...


class RepositorioProveedores(Protocol):
    """Memoria local de proveedor → concepto de retención, y decisiones del usuario."""

    def concepto_de_proveedor(self, nit: str) -> str | None: ...

    def asignar_concepto(self, nit: str, concepto: str) -> None: ...


class OcrProveedor(Protocol):
    """Extrae texto de un soporte físico (PDF o imagen). Es opcional en la aplicación."""

    def extraer_texto(self, ruta: Path) -> str: ...
