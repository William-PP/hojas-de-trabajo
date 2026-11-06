"""Pruebas del escritor: estructura de las pestañas, fórmulas vivas y copia intacta de `Dian`."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook

from dian_hojas.dominio.enums import Bloque
from dian_hojas.dominio.modelos import Cliente, Periodo, construir_resultado
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl, ErrorEscritura
from dian_hojas.infraestructura.plantilla import ENCABEZADOS, TITULO_GENERAL
from tests.herramientas.documentos import documento
from tests.herramientas.formulas import valor

CLIENTE = Cliente(nombre="Cliente Sintetico SAS", numero="1020396459")
PERIODO = Periodo(anio=2026, mes=10)


def escribir(tmp_path: Path, ruta_listado: Path, resultado=None) -> Path:
    if resultado is None:
        from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx

        resultado = construir_resultado(LectorDianXlsx().leer(ruta_listado).documentos)
    destino = tmp_path / "salida.xlsx"
    return EscritorOpenpyxl().escribir(
        resultado, CLIENTE, PERIODO, destino, ruta_listado=ruta_listado
    )


@pytest.fixture(scope="module")
def libro(tmp_path_factory, ruta_listado_sintetico):
    carpeta = tmp_path_factory.mktemp("escritor")
    ruta = escribir(carpeta, ruta_listado_sintetico)
    wb = load_workbook(ruta)
    yield wb
    wb.close()


# --- Estructura general ----------------------------------------------------------------


def test_pestanas_en_orden(libro):
    assert libro.sheetnames == ["Dian", "Sumatorias", "Ventas", "Compras"]


def test_dian_es_una_copia_intacta(libro, ruta_listado_sintetico):
    fuente = load_workbook(ruta_listado_sintetico)
    try:
        origen = fuente["Dian"]
        copia = libro["Dian"]
        assert copia.freeze_panes == origen.freeze_panes
        assert copia.auto_filter.ref == origen.auto_filter.ref
        assert copia.max_row == origen.max_row
        for fila in range(1, origen.max_row + 1):
            for columna in range(1, 33):
                assert copia.cell(row=fila, column=columna).value == origen.cell(
                    row=fila, column=columna
                ).value, f"cambió {copia.cell(row=fila, column=columna).coordinate}"
    finally:
        fuente.close()


@pytest.mark.parametrize("hoja", ["Sumatorias", "Ventas", "Compras"])
def test_cabecera(libro, hoja):
    ws = libro[hoja]
    assert ws["E1"].value == "Cliente Sintetico SAS"
    assert ws["E2"].value == "NIT. 1.020.396.459"
    assert ws["E3"].value == "LISTADO DOCUMENTOS ELECTRONICOS DIAN OCTUBRE 2026"
    assert {str(m) for m in ws.merged_cells.ranges} == {"E1:S1", "E2:S2", "E3:S3"}
    assert [ws.cell(row=4, column=c).value for c in range(3, 21)] == list(ENCABEZADOS)
    assert ws.freeze_panes == "A5"


def test_anchos(libro):
    ws = libro["Sumatorias"]
    assert ws.column_dimensions["M"].width == pytest.approx(35.6)
    assert ws.column_dimensions["A"].width == pytest.approx(5.43)


# --- Sumatorias ------------------------------------------------------------------------


def test_sumatorias_titulo_general(libro):
    ws = libro["Sumatorias"]
    assert ws["C5"].value == TITULO_GENERAL
    assert ws["C6"].value is None


def test_sumatorias_bloques_y_filas(libro):
    ws = libro["Sumatorias"]
    assert ws["C7"].value == "FACTURAS DE VENTAS"
    assert ws["C8"].value == "Factura electrónica"
    assert ws["C9"].value == "Factura electrónica"
    assert ws["O10"].value == "TOTAL FACTURAS VENTAS"
    assert ws["C13"].value == "DEVOLUCIONES EN VENTAS"
    assert ws["O15"].value == "TOTAL DEVOLUCIONES EN VENTAS"
    assert ws["C18"].value == "FACTURAS DE COMPRAS"
    assert ws["O25"].value == "TOTAL FACTURAS DE COMPRAS"
    assert ws["C28"].value == "DEVOLUCIONES EN COMPRAS"
    assert ws["O31"].value == "TOTAL DEVOLUCIONES EN COMPRAS"
    assert ws["C34"].value == "NOMINA"
    assert ws["O36"].value == "TOTAL NOMINA"


def test_sumatorias_no_tiene_marcas_dian_fisica(libro):
    ws = libro["Sumatorias"]
    assert all(ws.cell(row=fila, column=1).value is None for fila in range(7, 37))
    assert all(ws.cell(row=fila, column=2).value is None for fila in range(7, 37))


def test_sumatorias_autofiltro_al_final(libro):
    ws = libro["Sumatorias"]
    assert ws.auto_filter.ref == f"C4:T{ws.max_row}"
    assert ws.max_row == 36


def test_sumatorias_totales(libro):
    ws = libro["Sumatorias"]
    assert ws["P10"].value == "=SUM(P8:P9)"
    assert ws["Q10"].value == "=SUM(Q8:Q9)"
    assert ws["R10"].value == "=SUM(R8:R9)"

    ventas = {letra: valor(ws, f"{letra}10") for letra in "PQR"}
    assert ventas == {"P": 87400.0, "Q": 510000.0, "R": 597400.0}

    devoluciones_ventas = {letra: valor(ws, f"{letra}15") for letra in "PQR"}
    assert devoluciones_ventas == {"P": 12000.0, "Q": 66000.0, "R": 78000.0}

    compras = {letra: valor(ws, f"{letra}25") for letra in "PQR"}
    assert compras == {"P": 28297.0, "Q": 674407.0, "R": 702704.0}

    devoluciones = {letra: valor(ws, f"{letra}31") for letra in "PQR"}
    assert devoluciones["R"] == pytest.approx(845801.76)
    assert devoluciones["Q"] == pytest.approx(710761.98)

    nomina = {letra: valor(ws, f"{letra}36") for letra in "PQR"}
    assert nomina == {"P": 0.0, "Q": 2259927.6, "R": 2259927.6}


def test_sumatorias_suma_de_bloques_igual_al_listado(libro, listado_sintetico):
    ws = libro["Sumatorias"]
    total_bloques = sum(valor(ws, f"R{fila}") for fila in (10, 15, 25, 31, 36))
    assert total_bloques == pytest.approx(float(listado_sintetico.total), abs=0.01)
    assert total_bloques == pytest.approx(4483833.36, abs=0.01)


def test_total_neto_es_formula(libro):
    ws = libro["Sumatorias"]
    assert ws["Q8"].value == "=R8-P8"
    assert valor(ws, "Q8") == pytest.approx(460000.0)


# --- Contenido de las filas de datos ---------------------------------------------------


def test_textos_copiados_tal_cual(libro):
    ws = libro["Sumatorias"]
    # Fila 8: la venta más reciente.
    assert ws["C8"].value == "Factura electrónica"
    assert ws["E8"].value == "197"
    assert ws["F8"].value == "FV"
    assert ws["J8"].value == "20-10-2026"
    assert ws["K8"].value == "2026-10-20T10:42:17"
    assert ws["L8"].value == "1020396459"
    assert ws["T8"].value == "Emitido"
    assert ws["S8"].value == "Aprobado con notificación"


def test_folio_con_ceros_y_letras(libro):
    ws = libro["Ventas"]
    folios = {ws.cell(row=fila, column=5).value for fila in (6, 7)}
    assert "000123" in folios


def test_orden_descendente_por_fecha_en_compras(libro):
    ws = libro["Compras"]
    fechas = [ws.cell(row=fila, column=10).value for fila in range(6, 12)]
    assert fechas == [
        "31-10-2026",
        "18-10-2026",
        "15-10-2026",
        "12-10-2026",
        "09-10-2026",
        "01-10-2026",
    ]


def test_dinero_en_columnas_p_r(libro):
    ws = libro["Compras"]
    assert ws["P6"].value == pytest.approx(26297.0)
    assert ws["Q6"].value == "=R6-P6"
    assert ws["R6"].value == pytest.approx(164704.0)
    assert ws["P6"].number_format == '"$"\\ #,##0;[Red]\\-"$"\\ #,##0'


# --- Ventas y Compras ------------------------------------------------------------------


def test_ventas_lleva_ventas_y_devoluciones(libro):
    ws = libro["Ventas"]
    assert ws["A5"].value == "DIAN"
    assert ws["B5"].value == "FISICA"
    assert ws["C5"].value == "FACTURAS DE VENTAS"
    assert [ws.cell(row=fila, column=3).value for fila in range(6, 9)] == [
        "Factura electrónica",
        "Factura electrónica",
        None,
    ]
    assert ws["O8"].value == "TOTAL FACTURAS VENTAS"
    assert ws["C11"].value == "DEVOLUCIONES EN VENTAS"
    assert ws["O13"].value == "TOTAL DEVOLUCIONES EN VENTAS"
    assert ws.max_row == 13


def test_marcas_dian_fisica(libro):
    esperado = {"Ventas": 3, "Compras": 9}
    for nombre, cuantas in esperado.items():
        ws = libro[nombre]
        filas = [
            fila
            for fila in range(6, ws.max_row + 1)
            if ws.cell(row=fila, column=1).value is not None
        ]
        assert len(filas) == cuantas, f"{nombre} debería tener {cuantas} filas de datos"
        for fila in filas:
            assert ws.cell(row=fila, column=1).value is True
            assert ws.cell(row=fila, column=2).value is False


def test_compras_lleva_los_tres_bloques(libro):
    ws = libro["Compras"]
    assert ws["C5"].value == "FACTURAS DE COMPRAS"
    assert ws["O12"].value == "TOTAL FACTURAS DE COMPRAS"
    assert ws["C15"].value == "DEVOLUCIONES EN COMPRAS"
    assert ws["O18"].value == "TOTAL DEVOLUCIONES EN COMPRAS"
    assert ws["C21"].value == "NOMINA"
    assert ws["O23"].value == "TOTAL NOMINA"


def test_documento_soporte_y_equivalente_van_en_compras(libro):
    ws = libro["Compras"]
    tipos = [ws.cell(row=fila, column=3).value for fila in range(6, 12)]
    assert "Documento soporte con no obligados" in tipos
    assert "Documento equivalente - Servicios públicos domiciliarios" in tipos


# --- Bloques vacíos y errores ----------------------------------------------------------


def test_bloques_vacios_se_omiten(tmp_path, ruta_listado_sintetico):
    solo_venta = construir_resultado(
        (
            documento(
                indice=0,
                cufe="v1",
                tipo_texto="Factura electrónica",
                grupo_texto="Emitido",
                fecha_emision=date(2026, 10, 10),
                nit_emisor="1020396459",
            ),
        )
    )
    ruta = escribir(tmp_path, ruta_listado_sintetico, solo_venta)
    wb = load_workbook(ruta)
    try:
        assert wb["Sumatorias"]["C7"].value == "FACTURAS DE VENTAS"
        assert wb["Sumatorias"]["C10"].value is None
        assert wb["Ventas"]["C5"].value == "FACTURAS DE VENTAS"
        # Compras queda sin bloques: solo la cabecera y los rótulos DIAN/FISICA.
        assert wb["Compras"]["C5"].value is None
        assert wb["Compras"].max_row == 5
    finally:
        wb.close()


def test_no_se_puede_sobrescribir_el_listado(tmp_path, ruta_listado_sintetico):
    from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx

    resultado = construir_resultado(LectorDianXlsx().leer(ruta_listado_sintetico).documentos)
    with pytest.raises(ErrorEscritura, match="mismo listado"):
        EscritorOpenpyxl().escribir(
            resultado, CLIENTE, PERIODO, ruta_listado_sintetico, ruta_listado=ruta_listado_sintetico
        )


def test_mes_sin_documentos_no_se_escribe(tmp_path, ruta_listado_sintetico):
    vacio = construir_resultado(())
    with pytest.raises(ErrorEscritura, match="no tiene documentos"):
        EscritorOpenpyxl().escribir(
            vacio, CLIENTE, PERIODO, tmp_path / "x.xlsx", ruta_listado=ruta_listado_sintetico
        )


def test_el_libro_generado_pide_recalcular(libro):
    assert libro.calculation.fullCalcOnLoad is True
