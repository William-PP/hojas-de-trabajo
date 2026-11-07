"""Cruce opcional entre el texto de un soporte físico y los documentos del mes.

Es lógica pura (sin OCR ni Qt): el adaptador de OCR entrega texto y aquí se decide qué documentos
aparecen en él. El cruce **no bloquea** la exportación: solo permite marcar `FISICA = TRUE` cuando
el usuario aporta el soporte.
"""

from __future__ import annotations

import unicodedata

from dian_hojas.dominio.modelos import DocumentoElectronico

LONGITUD_MINIMA_CUFE = 8
LONGITUD_MINIMA_FOLIO = 6


def normalizar_texto(texto: str) -> str:
    """Mayúsculas y solo letras/números: tolera espacios, guiones y tildes del OCR."""
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
    return "".join(caracter for caracter in sin_tildes.upper() if caracter.isalnum())


def documentos_en_texto(
    texto: str,
    documentos: tuple[DocumentoElectronico, ...] | list[DocumentoElectronico],
) -> tuple[DocumentoElectronico, ...]:
    """Documentos reconocibles en el texto, sin repetir y en el orden del listado.

    Se busca el CUFE completo o, para folios, `prefijo + folio`. Un folio suelto demasiado corto
    (por ejemplo `16`) no se usa: generaría falsos positivos en casi cualquier factura.
    """
    contenido = normalizar_texto(texto)
    if not contenido:
        return ()

    encontrados: list[DocumentoElectronico] = []
    vistos: set[str] = set()
    for documento in documentos:
        if documento.cufe in vistos:
            continue

        cufe = normalizar_texto(documento.cufe)
        prefijo_folio = normalizar_texto(f"{documento.prefijo}{documento.folio}")
        folio = normalizar_texto(documento.folio)

        coincide = (
            len(cufe) >= LONGITUD_MINIMA_CUFE and cufe in contenido
        ) or (
            len(prefijo_folio) >= LONGITUD_MINIMA_FOLIO and prefijo_folio in contenido
        ) or (
            len(folio) >= LONGITUD_MINIMA_FOLIO and folio in contenido
        )
        if coincide:
            encontrados.append(documento)
            vistos.add(documento.cufe)

    return tuple(encontrados)
