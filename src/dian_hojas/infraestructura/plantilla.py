"""Plantilla de las hojas de trabajo: qué bloques van, en qué orden y con qué literales.

Los literales son los canónicos de D-04 y el orden el de D-05. Nada de esto depende de openpyxl:
aquí solo se describe la estructura.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from dian_hojas.dominio.enums import Bloque

# Fila 4 de las tres hojas, columnas C a T (D-14 los compara tal cual).
ENCABEZADOS: tuple[str, ...] = (
    "Tipo de documento",
    "CUFE/CUDE",
    "Folio",
    "Prefijo",
    "Divisa",
    "Forma de Pago",
    "Medio de Pago",
    "Fecha Emisión",
    "Fecha Recepción",
    "NIT Emisor",
    "Nombre Emisor",
    "NIT Receptor",
    "Nombre Receptor",
    "IVA",
    "Total Neto",
    "Total",
    "Estado",
    "Grupo",
)

# Primera y última columna del bloque de datos (C y T).
COLUMNA_INICIAL = 3
COLUMNA_FINAL = 20

# Las filas 1 a 3 se combinan solo de E a S (D-15), no de C a T.
COLUMNA_TITULO_INICIAL = 5
COLUMNA_TITULO_FINAL = 19

# Columnas de dinero y la fila de totales.
COLUMNA_IVA = 16  # P
COLUMNA_TOTAL_NETO = 17  # Q
COLUMNA_TOTAL = 18  # R
COLUMNA_ETIQUETA_TOTAL = 15  # O

TITULO_GENERAL = "REVISION DEL TOTAL DE DOCUMENTOS Y SUMATORIAS"

ENCABEZADO_DIAN = "DIAN"
ENCABEZADO_FISICA = "FISICA"


class Hoja(StrEnum):
    """Pestañas de trabajo de la Fase 1."""

    SUMATORIAS = "Sumatorias"
    VENTAS = "Ventas"
    COMPRAS = "Compras"


@dataclass(frozen=True, slots=True)
class DefinicionBloque:
    bloque: Bloque
    titulo: str
    etiqueta_total: str


BLOQUES: dict[Bloque, DefinicionBloque] = {
    definicion.bloque: definicion
    for definicion in (
        DefinicionBloque(Bloque.FACTURAS_VENTAS, "FACTURAS DE VENTAS", "TOTAL FACTURAS VENTAS"),
        DefinicionBloque(
            Bloque.DEVOLUCIONES_VENTAS, "DEVOLUCIONES EN VENTAS", "TOTAL DEVOLUCIONES EN VENTAS"
        ),
        DefinicionBloque(
            Bloque.FACTURAS_COMPRAS, "FACTURAS DE COMPRAS", "TOTAL FACTURAS DE COMPRAS"
        ),
        DefinicionBloque(
            Bloque.DEVOLUCIONES_COMPRAS,
            "DEVOLUCIONES EN COMPRAS",
            "TOTAL DEVOLUCIONES EN COMPRAS",
        ),
        DefinicionBloque(Bloque.NOMINA, "NOMINA", "TOTAL NOMINA"),
    )
}

# Orden de aparición dentro de cada hoja (D-05).
ORDEN_SUMATORIAS: tuple[Bloque, ...] = (
    Bloque.FACTURAS_VENTAS,
    Bloque.DEVOLUCIONES_VENTAS,
    Bloque.FACTURAS_COMPRAS,
    Bloque.DEVOLUCIONES_COMPRAS,
    Bloque.NOMINA,
)

ORDEN_VENTAS: tuple[Bloque, ...] = (
    Bloque.FACTURAS_VENTAS,
    Bloque.DEVOLUCIONES_VENTAS,
)

ORDEN_COMPRAS: tuple[Bloque, ...] = (
    Bloque.FACTURAS_COMPRAS,
    Bloque.DEVOLUCIONES_COMPRAS,
    Bloque.NOMINA,
)


def bloques_de(hoja: Hoja) -> tuple[DefinicionBloque, ...]:
    """Definiciones de bloque que puede llevar una hoja, en su orden."""
    orden = {
        Hoja.SUMATORIAS: ORDEN_SUMATORIAS,
        Hoja.VENTAS: ORDEN_VENTAS,
        Hoja.COMPRAS: ORDEN_COMPRAS,
    }[hoja]
    return tuple(BLOQUES[bloque] for bloque in orden)


def hoja_lleva_marcas(hoja: Hoja) -> bool:
    """Solo `Ventas` y `Compras` llevan las casillas DIAN/FISICA en A y B."""
    return hoja in (Hoja.VENTAS, Hoja.COMPRAS)
