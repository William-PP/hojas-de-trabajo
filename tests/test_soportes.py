"""Pruebas del cruce opcional entre el texto de un soporte y los documentos del mes."""

from __future__ import annotations

from dian_hojas.dominio.soportes import documentos_en_texto, normalizar_texto
from tests.herramientas.documentos import documento


def test_normaliza_a_solo_alfanumerico_en_mayusculas() -> None:
    assert normalizar_texto("Factura N° 1-2 / ABC") == "FACTURAN12ABC"


def test_encuentra_por_cufe_aunque_el_texto_traiga_espacios() -> None:
    compra = documento(cufe="ABC123456789", folio="ZZZ1", prefijo="")
    texto = "Factura electronica ... abc 123 456 789 ... total"

    assert documentos_en_texto(texto, (compra,)) == (compra,)


def test_encuentra_por_folio_alfanumerico() -> None:
    nota = documento(tipo_texto="Nota de crédito electrónica", folio="NCP14858", prefijo="")
    texto = "NOTA CREDITO NCP 14858"

    assert documentos_en_texto(texto, (nota,)) == (nota,)


def test_encuentra_por_prefijo_y_folio_corto() -> None:
    compra = documento(cufe="OTRO-CUFE", folio="2002", prefijo="CFL")
    texto = "CFL-2002 del proveedor"

    assert documentos_en_texto(texto, (compra,)) == (compra,)


def test_no_confunde_un_folio_corto_suelto() -> None:
    compra = documento(cufe="OTRO-CUFE", folio="16", prefijo="")
    assert documentos_en_texto("documento numero 16 de prueba", (compra,)) == ()


def test_no_repite_un_documento_encontrado_dos_veces() -> None:
    compra = documento(cufe="ABC123456789", folio="ZZZ1", prefijo="")
    texto = "ABC123456789 ... ABC 123 456 789"

    assert documentos_en_texto(texto, (compra,)) == (compra,)


def test_sin_coincidencias_devuelve_tupla_vacia() -> None:
    compra = documento(cufe="ABC123456789", folio="ZZZ1", prefijo="")
    assert documentos_en_texto("texto de otra factura", (compra,)) == ()
