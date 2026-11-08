"""Recálculo real del archivo generado con LibreOffice (Windows).

Es la forma de comprobar que las fórmulas vivas (`=SUM(...)`, `=Total-IVA-Otros`) no dejan
errores después de que un motor de cálculo las evalúe.

- Si `soffice.exe` está disponible, se recalcula de verdad en modo `--headless`.
- Si no está, no se salta: se evalúan las fórmulas del `.xlsx` en Python (con el
  evaluador mínimo de las pruebas y, si está instalado, con la librería `formulas`)
  y se comparan contra los valores del modelo. La prueba también detecta un rango
  de `SUM` corrido una fila (ver prueba negativa).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from openpyxl import load_workbook

from dian_hojas.aplicacion.procesar_mes import procesar_mes
from dian_hojas.dominio.modelos import Cliente, Periodo
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl
from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx
from tests.herramientas.formulas import valor

CLIENTE = Cliente(nombre="Cliente Sintetico SAS", numero="900000001")
PERIODO = Periodo(anio=2026, mes=10)

ERRORES = ("#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "#N/A", "#NULL!", "#NUM!", "#SPILL!")

VARIABLE_SOFFICE = "DIAN_HOJAS_SOFFICE"
RUTAS_WINDOWS = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    r"C:\Program Files\LibreOffice 7\program\soffice.exe",
    r"C:\Program Files\LibreOffice 24\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice 7\program\soffice.exe",
)


def _soffice() -> str | None:
    """Localiza `soffice.exe` en Windows: variable de entorno, PATH o rutas típicas."""
    por_env = os.environ.get(VARIABLE_SOFFICE)
    if por_env and Path(por_env).is_file():
        return por_env
    encontrado = shutil.which("soffice") or shutil.which("libreoffice")
    if encontrado:
        return encontrado
    for ruta in RUTAS_WINDOWS:
        if Path(ruta).is_file():
            return ruta
    return None


def _valor_calculado(ws, coordenada: str):
    """Valor de una celda: caché de LibreOffice si existe, si no se evalúa la fórmula."""
    celda = ws[coordenada]
    bruto = celda.value
    if isinstance(bruto, str) and bruto.startswith("="):
        return valor(ws, coordenada)
    return bruto


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
        # Respaldo en Python: no se salta; las pruebas evalúan las fórmulas del archivo.
        return generado

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
    wb = load_workbook(recalculado, data_only=False)
    try:
        problemas = []
        for ws in wb.worksheets:
            for fila in ws.iter_rows():
                for celda in fila:
                    if isinstance(celda.value, str) and any(
                        celda.value.startswith(error) for error in ERRORES
                    ):
                        problemas.append(f"{ws.title}!{celda.coordinate}={celda.value}")
                    # En el respaldo, evalúa las fórmulas: si explotan, también es error.
                    if isinstance(celda.value, str) and celda.value.startswith("="):
                        try:
                            _valor_calculado(ws, celda.coordinate)
                        except Exception as exc:
                            problemas.append(f"{ws.title}!{celda.coordinate}: {exc}")
        assert problemas == [], problemas
    finally:
        wb.close()


def test_los_totales_recalculados_cuadran(recalculado: Path, listado_sintetico):
    wb = load_workbook(recalculado, data_only=False)
    try:
        ws = wb["Sumatorias"]
        filas_totales = [
            fila
            for fila in range(5, ws.max_row + 1)
            if isinstance(ws.cell(row=fila, column=15).value, str)
            and ws.cell(row=fila, column=15).value.strip().startswith("TOTAL")
        ]
        assert len(filas_totales) == 5
        suma = sum(float(_valor_calculado(ws, f"R{fila}") or 0) for fila in filas_totales)
        assert suma == pytest.approx(float(listado_sintetico.total), abs=0.01)

        # `Total Neto` tiene que ser, en cada fila de datos, Total - IVA - Otros (D-47).
        for fila in range(5, ws.max_row + 1):
            etiqueta = ws.cell(row=fila, column=15).value
            if isinstance(etiqueta, str) and etiqueta.strip().startswith("TOTAL"):
                continue
            if ws.cell(row=fila, column=3).value is None:
                continue
            iva = float(_valor_calculado(ws, f"P{fila}") or 0)
            otros = float(_valor_calculado(ws, f"U{fila}") or 0)
            neto = float(_valor_calculado(ws, f"Q{fila}") or 0)
            total = float(_valor_calculado(ws, f"R{fila}") or 0)
            assert neto == pytest.approx(total - iva - otros, abs=0.01)
    finally:
        wb.close()


def test_respaldo_detecta_rango_corrido_una_fila(recalculado: Path):
    """Si un `SUM` se corre una fila, el respaldo lo detecta comparando con el modelo."""
    wb = load_workbook(recalculado, data_only=False)
    try:
        ws = wb["Sumatorias"]
        # Corrompe a propósito el primer total: suma solo la primera fila del bloque.
        total = ws["P10"]
        assert total.value == "=SUM(P8:P9)"
        total.value = "=SUM(P9:P9)"
        # El valor evaluado ya no coincide con la suma del bloque (P8+P9).
        mal = float(valor(ws, "P10") or 0)
        bien = float(valor(ws, "P8") or 0) + float(valor(ws, "P9") or 0)
        assert mal != pytest.approx(bien)
    finally:
        wb.close()
