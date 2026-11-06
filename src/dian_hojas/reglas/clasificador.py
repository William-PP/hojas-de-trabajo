"""Clasificación de documentos por tipo y grupo.

La regla central: **primero el tipo, luego el grupo**. "Emitido" no significa venta.
"""

from __future__ import annotations

import unicodedata

from dian_hojas.dominio.enums import Categoria, Grupo, TipoDocumento

# (prefijo normalizado, tipo) — se compara con `startswith` para tolerar sufijos como
# "Documento equivalente - Servicios públicos domiciliarios".
_PREFIJOS_TIPO: tuple[tuple[str, TipoDocumento], ...] = (
    ("factura electronica", TipoDocumento.FACTURA),
    ("nota de credito electronica", TipoDocumento.NOTA_CREDITO),
    ("nota credito electronica", TipoDocumento.NOTA_CREDITO),
    ("documento soporte", TipoDocumento.DOCUMENTO_SOPORTE),
    ("documento equivalente", TipoDocumento.DOCUMENTO_EQUIVALENTE),
    ("nomina individual", TipoDocumento.NOMINA),
    ("nomina electronica", TipoDocumento.NOMINA),
    ("nomina", TipoDocumento.NOMINA),
    ("application response", TipoDocumento.RESPUESTA_DIAN),
)

_GRUPOS: dict[str, Grupo] = {
    "emitido": Grupo.EMITIDO,
    "recibido": Grupo.RECIBIDO,
}

# (tipo, grupo) -> categoría. Lo que no esté aquí termina en SIN_CLASIFICAR.
_CATEGORIAS: dict[tuple[TipoDocumento, Grupo], Categoria] = {
    (TipoDocumento.FACTURA, Grupo.EMITIDO): Categoria.VENTA,
    (TipoDocumento.FACTURA, Grupo.RECIBIDO): Categoria.COMPRA,
    (TipoDocumento.NOTA_CREDITO, Grupo.EMITIDO): Categoria.DEVOLUCION_VENTA,
    (TipoDocumento.NOTA_CREDITO, Grupo.RECIBIDO): Categoria.DEVOLUCION_COMPRA,
    # El documento soporte lo puede emitir o recibir el cliente; en ambos casos es costo.
    (TipoDocumento.DOCUMENTO_SOPORTE, Grupo.EMITIDO): Categoria.COMPRA,
    (TipoDocumento.DOCUMENTO_SOPORTE, Grupo.RECIBIDO): Categoria.COMPRA,
    (TipoDocumento.DOCUMENTO_EQUIVALENTE, Grupo.RECIBIDO): Categoria.COMPRA,
    (TipoDocumento.NOMINA, Grupo.EMITIDO): Categoria.NOMINA,
    # La respuesta de la DIAN no es un documento contable: se excluye y se reporta.
    (TipoDocumento.RESPUESTA_DIAN, Grupo.EMITIDO): Categoria.RESPUESTA_DIAN,
    (TipoDocumento.RESPUESTA_DIAN, Grupo.RECIBIDO): Categoria.RESPUESTA_DIAN,
}


def normalizar(texto: str | None) -> str:
    """Minúsculas, sin tildes, espacios colapsados."""
    if not texto:
        return ""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().split())


def tipo_de(tipo_texto: str | None) -> TipoDocumento | None:
    """Tipo de documento por prefijo. Devuelve None si no lo reconoce."""
    normalizado = normalizar(tipo_texto)
    for prefijo, tipo in _PREFIJOS_TIPO:
        if normalizado.startswith(prefijo):
            return tipo
    return None


def grupo_de(grupo_texto: str | None) -> Grupo | None:
    return _GRUPOS.get(normalizar(grupo_texto))


def clasificar(tipo_texto: str | None, grupo_texto: str | None) -> tuple[TipoDocumento | None, Categoria]:
    """Devuelve (tipo, categoría). Nunca lanza: lo desconocido es SIN_CLASIFICAR."""
    tipo = tipo_de(tipo_texto)
    if tipo is None:
        return None, Categoria.SIN_CLASIFICAR
    grupo = grupo_de(grupo_texto)
    if grupo is None:
        return tipo, Categoria.SIN_CLASIFICAR
    return tipo, _CATEGORIAS.get((tipo, grupo), Categoria.SIN_CLASIFICAR)
