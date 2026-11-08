"""Pruebas de los casos de uso: procesar el mes y exportar con nombre estándar."""

from __future__ import annotations

from decimal import Decimal

import pytest

from dian_hojas.aplicacion.exportar_hoja import (
    CuadreFallido,
    MesVacio,
    exportar_hoja,
)
from dian_hojas.aplicacion.procesar_mes import procesar_mes
from dian_hojas.dominio.modelos import Cliente, Periodo
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl
from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx
from tests.herramientas.listado_sintetico import crear_listado

CLIENTE = Cliente(nombre="Cliente Sintetico SAS", numero="900000001")
PERIODO = Periodo(anio=2026, mes=10)


def procesar(ruta, cliente=CLIENTE, periodo=PERIODO):
    return procesar_mes(ruta, cliente, periodo, LectorDianXlsx())


# --- procesar_mes ----------------------------------------------------------------------


def test_procesa_el_listado_completo(ruta_listado_sintetico):
    proceso = procesar(ruta_listado_sintetico)
    assert proceso.filas_dian == 13
    assert proceso.total_dian == Decimal("4483833.36")
    assert len(proceso.resultado.documentos) == 13
    assert not proceso.mes_vacio
    assert proceso.puede_exportar


def test_los_siete_cuadres_se_ejecutan(ruta_listado_sintetico):
    proceso = procesar(ruta_listado_sintetico)
    assert [c.codigo for c in proceso.cuadres] == ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    assert proceso.cuadres_fallidos == ()


def test_un_documento_desconocido_bloquea_la_exportacion(tmp_path):
    ruta = crear_listado(tmp_path / "raro.xlsx", desconocido=True)
    proceso = procesar(ruta)
    assert not proceso.puede_exportar
    codigos = {c.codigo for c in proceso.cuadres_fallidos}
    assert "C1" in codigos
    assert proceso.resultado.no_clasificados[0].folio == "RARO-1"


def test_una_fecha_fuera_del_mes_bloquea(tmp_path):
    ruta = crear_listado(tmp_path / "septiembre.xlsx", fuera_de_periodo=True)
    proceso = procesar(ruta)
    assert not proceso.puede_exportar
    assert "C5" in {c.codigo for c in proceso.cuadres_fallidos}


def test_otros_impuestos_bloquean(tmp_path):
    ruta = crear_listado(tmp_path / "inc.xlsx", otros_impuestos=True)
    proceso = procesar(ruta)
    assert proceso.puede_exportar
    assert "C7" in {c.codigo for c in proceso.alertas}
    assert "C7" not in {c.codigo for c in proceso.cuadres_fallidos}
    assert proceso.requiere_confirmacion_otros


def test_cufe_duplicado_bloquea(tmp_path):
    ruta = crear_listado(tmp_path / "dup.xlsx", duplicado=True)
    proceso = procesar(ruta)
    assert not proceso.puede_exportar
    assert "C3" in {c.codigo for c in proceso.cuadres_fallidos}


def test_cliente_que_no_aparece_bloquea(ruta_listado_sintetico):
    otro = Cliente(nombre="Otro Cliente", numero="900000000")
    proceso = procesar(ruta_listado_sintetico, cliente=otro)
    assert not proceso.puede_exportar
    assert "C6" in {c.codigo for c in proceso.cuadres_fallidos}


def test_mes_vacio(tmp_path):
    ruta = tmp_path / "vacio.xlsx"
    from openpyxl import Workbook

    from dian_hojas.infraestructura.lector_dian_xlsx import COLUMNAS_ESPERADAS

    wb = Workbook()
    ws = wb.active
    ws.title = "Dian"
    ws.append(list(COLUMNAS_ESPERADAS))
    wb.save(ruta)
    wb.close()

    proceso = procesar(ruta)
    assert proceso.mes_vacio
    assert not proceso.puede_exportar


# --- exportar_hoja ---------------------------------------------------------------------


def test_exporta_con_el_nombre_estandar(ruta_listado_sintetico, tmp_path):
    proceso = procesar(ruta_listado_sintetico)
    carpeta = tmp_path / "salida"
    ruta = exportar_hoja(proceso, CLIENTE, PERIODO, carpeta, EscritorOpenpyxl())
    assert ruta.parent == carpeta
    assert ruta.name == "10-Hoja_de_trabajo_Rtefte_Oct_2026_Cliente_Sintetico_SAS.xlsx"
    assert ruta.is_file()


def test_no_exporta_si_un_cuadre_falla(tmp_path):
    ruta_listado = crear_listado(tmp_path / "raro.xlsx", desconocido=True)
    proceso = procesar(ruta_listado)
    carpeta = tmp_path / "salida"
    with pytest.raises(CuadreFallido) as info:
        exportar_hoja(proceso, CLIENTE, PERIODO, carpeta, EscritorOpenpyxl())
    assert "C1" in str(info.value)
    assert list(carpeta.glob("*.xlsx")) == []


def test_no_exporta_un_mes_vacio(tmp_path):
    from openpyxl import Workbook

    from dian_hojas.infraestructura.lector_dian_xlsx import COLUMNAS_ESPERADAS

    ruta = tmp_path / "vacio.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Dian"
    ws.append(list(COLUMNAS_ESPERADAS))
    wb.save(ruta)
    wb.close()

    proceso = procesar(ruta)
    with pytest.raises(MesVacio):
        exportar_hoja(proceso, CLIENTE, PERIODO, tmp_path / "salida", EscritorOpenpyxl())


def test_cuadre_fallido_lleva_el_detalle(tmp_path):
    ruta_listado = crear_listado(tmp_path / "raro.xlsx", desconocido=True)
    proceso = procesar(ruta_listado)
    with pytest.raises(CuadreFallido) as info:
        exportar_hoja(proceso, CLIENTE, PERIODO, tmp_path / "salida", EscritorOpenpyxl())
    assert "C1" in str(info.value)


def test_exportar_con_otros_requiere_confirmacion(tmp_path):
    from dian_hojas.aplicacion.exportar_hoja import ConfirmacionRequerida
    from openpyxl import load_workbook

    ruta_listado = crear_listado(tmp_path / "inc.xlsx", otros_impuestos=True)
    proceso = procesar(ruta_listado)
    assert proceso.requiere_confirmacion_otros
    with pytest.raises(ConfirmacionRequerida):
        exportar_hoja(proceso, CLIENTE, PERIODO, tmp_path / "salida", EscritorOpenpyxl())
    assert list((tmp_path / "salida").glob("*.xlsx")) == []

    ruta = exportar_hoja(
        proceso,
        CLIENTE,
        PERIODO,
        tmp_path / "salida",
        EscritorOpenpyxl(),
        confirmar_otros_impuestos=True,
    )
    wb = load_workbook(ruta, data_only=False)
    try:
        ws = wb["Sumatorias"]
        assert ws["C1"].value is not None and "C7" in str(ws["C1"].value)
        assert ws["U4"].value == "Otros impuestos"
    finally:
        wb.close()


def test_salida_existente_no_sobrescribe(ruta_listado_sintetico, tmp_path):
    proceso = procesar(ruta_listado_sintetico)
    carpeta = tmp_path / "salida"
    primera = exportar_hoja(proceso, CLIENTE, PERIODO, carpeta, EscritorOpenpyxl())
    segunda = exportar_hoja(proceso, CLIENTE, PERIODO, carpeta, EscritorOpenpyxl())
    assert primera.is_file() and segunda.is_file()
    assert primera != segunda and segunda.name.endswith("_v2.xlsx")
