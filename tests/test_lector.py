"""Pruebas del lector del listado de la DIAN.

Cubren lo que puede venir mal: encabezados, tipos, fechas, archivos vacíos y archivos que
no son el listado. Un archivo mal leído nunca debe pasar en silencio.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from dian_hojas.dominio.enums import Categoria, TipoDocumento
from dian_hojas.infraestructura.lector_dian_xlsx import (
    COLUMNAS_ESPERADAS,
    ErrorListado,
    LectorDianXlsx,
    sin_clasificar,
)
from tests.herramientas.listado_sintetico import FILAS_BASE

TOTAL_SINTETICO = Decimal("4483833.36")
IVA_SINTETICO = Decimal("262736.78")


def leer(ruta: Path):
    return LectorDianXlsx().leer(ruta)


def variante(ruta_origen: Path, ruta_destino: Path, cambios: dict[str, object]) -> Path:
    """Copia el listado cambiando celdas sueltas, para probar un error puntual."""
    wb = load_workbook(ruta_origen)
    try:
        ws = wb["Dian"]
        for celda, valor in cambios.items():
            ws[celda] = valor
        wb.save(ruta_destino)
    finally:
        wb.close()
    return ruta_destino


# --- Lectura correcta -------------------------------------------------------------------


def test_lee_todas_las_filas(listado_sintetico):
    assert listado_sintetico.filas == len(FILAS_BASE) == 13
    assert len(listado_sintetico.documentos) == 13
    assert not listado_sintetico.vacio


def test_totales_del_listado(listado_sintetico):
    assert listado_sintetico.total == TOTAL_SINTETICO
    assert listado_sintetico.iva == IVA_SINTETICO
    assert listado_sintetico.impuestos_otros == 0


def test_categorias(listado_sintetico):
    conteo = {}
    for documento in listado_sintetico.documentos:
        conteo[documento.categoria] = conteo.get(documento.categoria, 0) + 1
    assert conteo == {
        Categoria.VENTA: 2,
        Categoria.COMPRA: 6,
        Categoria.DEVOLUCION_COMPRA: 2,
        Categoria.DEVOLUCION_VENTA: 1,
        Categoria.NOMINA: 1,
        Categoria.RESPUESTA_DIAN: 1,
    }


def test_folio_y_nit_se_conservan_como_texto(listado_sintetico):
    por_folio = {d.folio: d for d in listado_sintetico.documentos}

    assert "000123" in por_folio, "se perdió el cero a la izquierda del folio"
    assert "NCP14858" in por_folio
    assert "C0039827" in por_folio

    venta = por_folio["197"]
    assert venta.nit_emisor == "900000001"
    assert isinstance(venta.nit_emisor, str)
    assert isinstance(venta.folio, str)


def test_fechas(listado_sintetico):
    por_folio = {d.folio: d for d in listado_sintetico.documentos}

    nomina = por_folio["9"]
    assert nomina.fecha_emision == date(2026, 10, 1)
    assert nomina.fecha_recepcion == datetime(2026, 10, 1, 15, 58, 54)

    compra = por_folio["2002"]
    assert compra.fecha_emision == date(2026, 10, 31)


def test_fecha_con_dia_de_un_digito(tmp_path, ruta_listado_sintetico):
    copia = variante(
        ruta_listado_sintetico, tmp_path / "fecha.xlsx", {"H2": "1-10-2026"}
    )
    assert leer(copia).documentos[0].fecha_emision == date(2026, 10, 1)


def test_documento_soporte_emitido_es_compra(listado_sintetico):
    soporte = next(d for d in listado_sintetico.documentos if d.folio == "35")
    assert soporte.grupo_texto == "Emitido"
    assert soporte.categoria is Categoria.COMPRA


def test_respuesta_dian_se_lee_y_se_marca(listado_sintetico):
    respuestas = [d for d in listado_sintetico.documentos if d.tipo is TipoDocumento.RESPUESTA_DIAN]
    assert len(respuestas) == 1
    assert respuestas[0].categoria is Categoria.RESPUESTA_DIAN


def test_sin_clasificar_no_descarta(tmp_path, ruta_listado_sintetico):
    from tests.herramientas.listado_sintetico import crear_listado

    ruta = crear_listado(tmp_path / "raro.xlsx", desconocido=True)
    listado = leer(ruta)
    assert listado.filas == 14
    assert [d.folio for d in sin_clasificar(listado)] == ["RARO-1"]


def test_duplicado_se_lee_y_lo_detecta_el_cuadre(tmp_path):
    from tests.herramientas.listado_sintetico import crear_listado

    listado = leer(crear_listado(tmp_path / "dup.xlsx", duplicado=True))
    assert listado.filas == 14
    assert len({d.cufe for d in listado.documentos}) == 13


def test_indice_respeta_el_orden_del_archivo(listado_sintetico):
    assert [d.indice for d in listado_sintetico.documentos] == list(range(13))


def test_otros_impuestos_se_suman(tmp_path):
    from tests.herramientas.listado_sintetico import crear_listado

    listado = leer(crear_listado(tmp_path / "inc.xlsx", otros_impuestos=True))
    assert listado.impuestos_otros == Decimal("5000.00")


# --- Validación -------------------------------------------------------------------------


def test_archivo_inexistente(tmp_path):
    with pytest.raises(ErrorListado, match="No existe el archivo"):
        leer(tmp_path / "no-existe.xlsx")


def test_archivo_solo_encabezados_es_vacio(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Dian"
    ws.append(list(COLUMNAS_ESPERADAS))
    ruta = tmp_path / "vacio.xlsx"
    wb.save(ruta)
    wb.close()

    listado = leer(ruta)
    assert listado.vacio
    assert listado.documentos == ()
    assert listado.total == 0


def test_encabezado_cambiado(tmp_path, ruta_listado_sintetico):
    copia = variante(ruta_listado_sintetico, tmp_path / "h.xlsx", {"A1": "Tipo"})
    with pytest.raises(ErrorListado, match="Encabezado inesperado en A1"):
        leer(copia)


def test_encabezados_desordenados(tmp_path, ruta_listado_sintetico):
    copia = variante(
        ruta_listado_sintetico,
        tmp_path / "orden.xlsx",
        {"C1": "Prefijo", "D1": "Folio"},
    )
    with pytest.raises(ErrorListado, match="Encabezado inesperado en C1"):
        leer(copia)


def test_columna_adicional_al_final_no_estorba(tmp_path, ruta_listado_sintetico):
    copia = variante(ruta_listado_sintetico, tmp_path / "extra.xlsx", {"AG1": "Comentario"})
    assert leer(copia).filas == 13


def test_fecha_invalida(tmp_path, ruta_listado_sintetico):
    copia = variante(ruta_listado_sintetico, tmp_path / "f.xlsx", {"H3": "31-02-2026"})
    with pytest.raises(ErrorListado) as info:
        leer(copia)
    mensaje = str(info.value)
    assert "Fila 3" in mensaje
    assert "Fecha Emisión" in mensaje


def test_nit_numerico_es_un_error_explicado(tmp_path, ruta_listado_sintetico):
    copia = variante(ruta_listado_sintetico, tmp_path / "n.xlsx", {"J2": 900123456})
    with pytest.raises(ErrorListado) as info:
        leer(copia)
    mensaje = str(info.value)
    assert "NIT Emisor" in mensaje
    assert "número" in mensaje


def test_folio_numerico_es_un_error_explicado(tmp_path, ruta_listado_sintetico):
    copia = variante(ruta_listado_sintetico, tmp_path / "fol.xlsx", {"C2": 197})
    with pytest.raises(ErrorListado, match="Folio"):
        leer(copia)


def test_total_no_numerico(tmp_path, ruta_listado_sintetico):
    copia = variante(ruta_listado_sintetico, tmp_path / "t.xlsx", {"AD2": "mil pesos"})
    with pytest.raises(ErrorListado, match="Total"):
        leer(copia)


def test_fila_vacia_se_ignora(tmp_path, ruta_listado_sintetico):
    copia = variante(ruta_listado_sintetico, tmp_path / "blanco.xlsx", {"A15": None})
    assert leer(copia).filas == 13


def test_hoja_llamada_distinto_usa_la_primera(tmp_path, ruta_listado_sintetico):
    wb = load_workbook(ruta_listado_sintetico)
    try:
        wb["Dian"].title = "Listado"
        ruta = tmp_path / "otra.xlsx"
        wb.save(ruta)
    finally:
        wb.close()
    assert leer(ruta).filas == 13
