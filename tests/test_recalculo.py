"""Recálculo real del archivo generado con LibreOffice.

Es la única forma de comprobar que las fórmulas vivas (`=SUM(...)`, `=R8-P8`) no dejan errores
después de que un motor de cálculo las evalúe. Si LibreOffice no está instalado, la prueba se
salta: no se finge el resultado.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from openpyxl import load_workbook

from dian_hojas.aplicacion.procesar_mes import procesar_mes
from dian_hojas.dominio.modelos import Cliente, Periodo
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl
from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx

CLIENTE = Cliente(nombre="Cliente Sintetico SAS", numero="1020396459")
PERIODO = Periodo(anio=2026, mes=10)

ERRORES = ("#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#N/A", "#NULL!", "#NUM!", "#SPILL!")

RUTAS_WINDOWS = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
)


def _soffice() -> str | None:
    encontrado = shutil.which("soffice") or shutil.which("libreoffice")
    if encontrado:
        return encontrado
    for ruta in RUTAS_WINDOWS:
        if Path(ruta).is_file():
            return ruta
    return None


@pytest.fixture(scope="module")
def generado(tmp_path_factory, ruta_listado_sintetico) -> Path:
    proceso = procesar_mes(ruta_listado_sintetico, CLIENTE, PERIODO, LectorDianXlsx())
    assert proceso.puede_exportar, [c.detalle for c in proceso.cuadres_fallidos]
    destino = tmp_path_factory.mktemp("recalculo") / "hoja.xlsx"
    return EscritorOpenpyxl().escribir(
        proceso.resultado,
        CLIENTE,
        PERIODO,
        destino,
        ruta_listado=ruta_listado_sintetico,
    )


@pytest.fixture(scope="module")
def recalculado(generado: Path, tmp_path_factory) -> Path:
    soffice = _soffice()
    if soffice is None:
        pytest.skip("LibreOffice no está instalado: no se puede recalcular de verdad")

    salida = tmp_path_factory.mktemp("recalculado")
    subprocess.run(
        [
            soffice,
            "--headless",
            "--calc",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(salida),
            str(generado),
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )
    destino = salida / generado.name
    if not destino.is_file():
        pytest.fail("LibreOffice no generó el archivo recalculado")
    return destino


def test_no_quedan_errores_de_formula(recalculado: Path):
    wb = load_workbook(recalculado, data_only=True)
    try:
        problemas = []
        for ws in wb.worksheets:
            for fila in ws.iter_rows():
                for celda in fila:
                    if isinstance(celda.value, str) and any(
                        celda.value.startswith(error) for error in ERRORES
                    ):
                        problemas.append(f"{ws.title}!{celda.coordinate}={celda.value}")
        assert problemas == [], problemas
    finally:
        wb.close()


def test_los_totales_recalculados_cuadran(recalculado: Path, listado_sintetico):
    wb = load_workbook(recalculado, data_only=True)
    try:
        ws = wb["Sumatorias"]
        filas_totales = [
            fila
            for fila in range(5, ws.max_row + 1)
            if isinstance(ws.cell(row=fila, column=15).value, str)
            and ws.cell(row=fila, column=15).value.strip().startswith("TOTAL")
        ]
        assert len(filas_totales) == 5
        suma = sum(float(ws.cell(row=fila, column=18).value or 0) for fila in filas_totales)
        assert suma == pytest.approx(float(listado_sintetico.total), abs=0.01)

        # `Total Neto` tiene que ser, en cada fila de datos, el Total menos el IVA.
        for fila in range(5, ws.max_row + 1):
            etiqueta = ws.cell(row=fila, column=15).value
            if isinstance(etiqueta, str) and etiqueta.strip().startswith("TOTAL"):
                continue
            if ws.cell(row=fila, column=3).value is None:
                continue
            iva = float(ws.cell(row=fila, column=16).value or 0)
            neto = float(ws.cell(row=fila, column=17).value or 0)
            total = float(ws.cell(row=fila, column=18).value or 0)
            assert neto == pytest.approx(total - iva, abs=0.01)
    finally:
        wb.close()
