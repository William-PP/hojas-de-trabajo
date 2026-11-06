"""Pruebas del clasificador: cada combinación tipo/grupo y los casos borde."""

import pytest

from dian_hojas.dominio.enums import Categoria, Grupo, TipoDocumento
from dian_hojas.reglas.clasificador import clasificar, grupo_de, normalizar, tipo_de


@pytest.mark.parametrize(
    ("tipo_texto", "grupo_texto", "tipo_esperado", "categoria_esperada"),
    [
        ("Factura electrónica", "Emitido", TipoDocumento.FACTURA, Categoria.VENTA),
        ("Factura electrónica", "Recibido", TipoDocumento.FACTURA, Categoria.COMPRA),
        ("Documento soporte con no obligados", "Emitido", TipoDocumento.DOCUMENTO_SOPORTE, Categoria.COMPRA),
        ("Documento soporte con no obligados", "Recibido", TipoDocumento.DOCUMENTO_SOPORTE, Categoria.COMPRA),
        (
            "Documento equivalente - Servicios públicos domiciliarios",
            "Recibido",
            TipoDocumento.DOCUMENTO_EQUIVALENTE,
            Categoria.COMPRA,
        ),
        (
            "Documento equivalente - Servicios públicos domiciliarios",
            "Emitido",
            TipoDocumento.DOCUMENTO_EQUIVALENTE,
            Categoria.SIN_CLASIFICAR,
        ),
        ("Nota de crédito electrónica", "Recibido", TipoDocumento.NOTA_CREDITO, Categoria.DEVOLUCION_COMPRA),
        ("Nota de crédito electrónica", "Emitido", TipoDocumento.NOTA_CREDITO, Categoria.DEVOLUCION_VENTA),
        ("Nomina Individual", "Emitido", TipoDocumento.NOMINA, Categoria.NOMINA),
        ("Nomina Individual", "Recibido", TipoDocumento.NOMINA, Categoria.SIN_CLASIFICAR),
        ("Application response", "Recibido", TipoDocumento.RESPUESTA_DIAN, Categoria.RESPUESTA_DIAN),
        ("Application response", "Emitido", TipoDocumento.RESPUESTA_DIAN, Categoria.RESPUESTA_DIAN),
        ("Documento raro de otro país", "Emitido", None, Categoria.SIN_CLASIFICAR),
        ("Factura electrónica", "Otro grupo", TipoDocumento.FACTURA, Categoria.SIN_CLASIFICAR),
        ("Factura electrónica", "", TipoDocumento.FACTURA, Categoria.SIN_CLASIFICAR),
        ("Factura electrónica", None, TipoDocumento.FACTURA, Categoria.SIN_CLASIFICAR),
        (None, "Emitido", None, Categoria.SIN_CLASIFICAR),
    ],
)
def test_clasificar(tipo_texto, grupo_texto, tipo_esperado, categoria_esperada):
    assert clasificar(tipo_texto, grupo_texto) == (tipo_esperado, categoria_esperada)


@pytest.mark.parametrize(
    "tipo_texto",
    [
        "  FACTURA ELECTRÓNICA  ",
        "factura electronica",
        "Factura  Electrónica",
        "FACTURA ELECTRONICA",
    ],
)
def test_tipo_tolera_tildes_mayusculas_y_espacios(tipo_texto):
    assert tipo_de(tipo_texto) is TipoDocumento.FACTURA


def test_normalizar():
    assert normalizar("  Nota   de Crédito  ") == "nota de credito"
    assert normalizar("DOCUMENTO EQUIVALENTE - Servicios Públicos") == "documento equivalente - servicios publicos"
    assert normalizar(None) == ""
    assert normalizar("") == ""


def test_grupo_de():
    assert grupo_de(" Emitido ") is Grupo.EMITIDO
    assert grupo_de("recibido") is Grupo.RECIBIDO
    assert grupo_de("Emitida") is None
    assert grupo_de(None) is None


def test_nunca_lanza_con_entradas_extranas():
    assert clasificar("", "") == (None, Categoria.SIN_CLASIFICAR)
    assert clasificar("   ", "   ") == (None, Categoria.SIN_CLASIFICAR)
