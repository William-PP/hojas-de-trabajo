"""Enumeraciones y taxonomía de documentos.

Python puro: este módulo no importa nada fuera de la biblioteca estándar.
"""

from enum import StrEnum


class TipoDocumento(StrEnum):
    """Tipo de documento electrónico, ya normalizado."""

    FACTURA = "FACTURA"
    NOTA_CREDITO = "NOTA_CREDITO"
    DOCUMENTO_SOPORTE = "DOCUMENTO_SOPORTE"
    DOCUMENTO_EQUIVALENTE = "DOCUMENTO_EQUIVALENTE"
    NOMINA = "NOMINA"
    RESPUESTA_DIAN = "RESPUESTA_DIAN"


class Grupo(StrEnum):
    """Quién emitió el documento respecto al cliente."""

    EMITIDO = "EMITIDO"
    RECIBIDO = "RECIBIDO"


class Categoria(StrEnum):
    """Destino contable del documento dentro de la hoja de trabajo."""

    VENTA = "VENTA"
    COMPRA = "COMPRA"
    DEVOLUCION_COMPRA = "DEVOLUCION_COMPRA"
    DEVOLUCION_VENTA = "DEVOLUCION_VENTA"
    NOMINA = "NOMINA"
    RESPUESTA_DIAN = "RESPUESTA_DIAN"
    SIN_CLASIFICAR = "SIN_CLASIFICAR"


class Bloque(StrEnum):
    """Bloque de la hoja de trabajo al que pertenece una categoría."""

    FACTURAS_VENTAS = "FACTURAS_VENTAS"
    DEVOLUCIONES_VENTAS = "DEVOLUCIONES_VENTAS"
    FACTURAS_COMPRAS = "FACTURAS_COMPRAS"
    DEVOLUCIONES_COMPRAS = "DEVOLUCIONES_COMPRAS"
    NOMINA = "NOMINA"


BLOQUE_POR_CATEGORIA: dict[Categoria, Bloque] = {
    Categoria.VENTA: Bloque.FACTURAS_VENTAS,
    Categoria.DEVOLUCION_VENTA: Bloque.DEVOLUCIONES_VENTAS,
    Categoria.COMPRA: Bloque.FACTURAS_COMPRAS,
    Categoria.DEVOLUCION_COMPRA: Bloque.DEVOLUCIONES_COMPRAS,
    Categoria.NOMINA: Bloque.NOMINA,
}


def bloque_de(categoria: Categoria) -> Bloque | None:
    """Bloque de hoja para una categoría, o None si no va a ninguna hoja."""
    return BLOQUE_POR_CATEGORIA.get(categoria)
