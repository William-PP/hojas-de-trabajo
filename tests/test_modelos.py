"""Pruebas de los modelos: totales, periodo, identificación y agrupación."""

from datetime import date
from decimal import Decimal

import pytest

from dian_hojas.dominio.enums import Bloque
from dian_hojas.dominio.modelos import Cliente, Periodo, agrupar_en_bloques, construir_resultado
from tests.herramientas.documentos import documento


def test_total_neto():
    doc = documento(iva=Decimal("1900.00"), total=Decimal("11900.00"))
    assert doc.total_neto == Decimal("10000.00")


def test_periodo_titulo_y_abreviatura():
    periodo = Periodo(anio=2026, mes=10)
    assert periodo.titulo == "LISTADO DOCUMENTOS ELECTRONICOS DIAN OCTUBRE 2026"
    assert periodo.mes_abrev == "Oct"


@pytest.mark.parametrize(
    ("anio", "mes", "ultimo"),
    [(2026, 2, date(2026, 2, 28)), (2024, 2, date(2024, 2, 29)), (2026, 4, date(2026, 4, 30))],
)
def test_periodo_ultimo_dia(anio, mes, ultimo):
    periodo = Periodo(anio=anio, mes=mes)
    assert periodo.primer_dia == date(anio, mes, 1)
    assert periodo.ultimo_dia == ultimo


def test_periodo_contiene():
    periodo = Periodo(anio=2026, mes=10)
    assert periodo.contiene(date(2026, 10, 31))
    assert not periodo.contiene(date(2026, 9, 30))
    assert not periodo.contiene(date(2025, 10, 1))


def test_nombre_archivo():
    cliente = Cliente(nombre="Cliente Demo S.A.S.", numero="901320747", digito_verificacion="4")
    assert Periodo(anio=2026, mes=10).nombre_archivo(cliente) == (
        "10-Hoja_de_trabajo_Rtefte_Oct_2026_Cliente_Demo_S.A.S..xlsx"
    )


def test_identificacion_nit():
    cliente = Cliente(nombre="Cliente", numero="901320747", digito_verificacion="4")
    assert cliente.identificacion_formateada == "NIT. 901.320.747-4"


def test_identificacion_cedula():
    cliente = Cliente(nombre="Cliente", tipo_identificacion="CC", numero="1020396459")
    assert cliente.identificacion_formateada == "CC. 1.020.396.459"


def test_identificacion_acepta_puntos():
    cliente = Cliente(nombre="Cliente", numero="901.320.747", digito_verificacion="4")
    assert cliente.identificacion_formateada == "NIT. 901.320.747-4"


def test_agrupar_ordena_por_fecha_descendente():
    documentos = (
        documento(indice=0, cufe="a", fecha_emision=date(2026, 10, 1)),
        documento(indice=1, cufe="b", fecha_emision=date(2026, 10, 20)),
        documento(indice=2, cufe="c", fecha_emision=date(2026, 10, 10)),
    )
    bloques = agrupar_en_bloques(documentos)
    assert [d.cufe for d in bloques[Bloque.FACTURAS_COMPRAS]] == ["b", "c", "a"]


def test_agrupar_respeta_orden_del_listado_en_fechas_iguales():
    documentos = (
        documento(indice=5, cufe="quinto", fecha_emision=date(2026, 10, 10)),
        documento(indice=1, cufe="primero", fecha_emision=date(2026, 10, 10)),
    )
    bloques = agrupar_en_bloques(documentos)
    assert [d.cufe for d in bloques[Bloque.FACTURAS_COMPRAS]] == ["primero", "quinto"]


def test_construir_resultado_separa_excluidos_y_sin_clasificar():
    documentos = (
        documento(indice=0, cufe="venta", tipo_texto="Factura electrónica", grupo_texto="Emitido"),
        documento(indice=1, cufe="respuesta", tipo_texto="Application response", grupo_texto="Recibido"),
        documento(indice=2, cufe="raro", tipo_texto="Documento raro", grupo_texto="Emitido"),
    )
    resultado = construir_resultado(documentos)
    assert [d.cufe for d in resultado.excluidos] == ["respuesta"]
    assert [d.cufe for d in resultado.no_clasificados] == ["raro"]
    assert [d.cufe for d in resultado.en_hoja] == ["venta"]


def test_totales_del_resultado():
    documentos = (
        documento(indice=0, cufe="a", iva=Decimal("100"), total=Decimal("1100")),
        documento(indice=1, cufe="b", iva=Decimal("200"), total=Decimal("2200")),
    )
    resultado = construir_resultado(documentos)
    assert resultado.total == Decimal("3300")
    assert resultado.iva == Decimal("300")
    assert resultado.total_neto == Decimal("3000")
