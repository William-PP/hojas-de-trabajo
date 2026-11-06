"""Prueba de integración contra las hojas de referencia reales.

Se salta sola si `Referencias/` no está (no se versiona). La comparación ignora, como dice D-14:
columnas A/B, texto exacto de las fórmulas, anchos, colores y las filas vacías de `Dian`;
y compara los documentos de cada bloque como multiconjunto, porque la referencia no sigue un
orden estricto por fecha (D-22).

Las referencias están **anonimizadas** (D-23): los NIT y los nombres de los documentos son `x`,
mientras que la cabecera de `Sumatorias` sí conserva el cliente real. Por eso el cuadre C6 no se
puede validar sobre ellas y se comprueba que falla con un detalle claro. La referencia #3 además
trae dos facturas con INC real (D-24): C7 debe marcarlas y bloquear la exportación, que es
exactamente el comportamiento pedido en D-19. Para comparar la estructura se usa el escritor
directamente, sin pasar por la validación que (correctamente) bloquea.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

import pytest
from openpyxl import load_workbook

from dian_hojas.aplicacion.procesar_mes import procesar_mes
from dian_hojas.dominio.modelos import Cliente, Periodo
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl
from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx
from tests.herramientas.formulas import valor

pytestmark = pytest.mark.referencias

REFERENCIA_GOLDEN = "3-Hoja de trabajo Rtefte Oct.2026.xlsm"
REFERENCIAS = (
    "1-Hoja de trabajo Rtefte Oct.2026 .xlsm",
    "2-Hoja de trabajo Rtefte Sep.2026.xlsm",
    "3-Hoja de trabajo Rtefte Oct.2026.xlsm",
)

COLUMNAS_DATOS = range(3, 21)  # C..T
COLUMNAS_DINERO = (16, 17, 18)  # P, Q, R

MESES = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}


@dataclass(frozen=True)
class Bloque:
    titulo: str
    filas: tuple[tuple, ...]
    total: tuple | None


def _referencia_filtro(cadena: str | None) -> str:
    """Normaliza `$C$4:$T$10` y `C4:T10`, que openpyxl guarda de una u otra forma."""
    return (cadena or "").replace("$", "")


def _mismo_valor(a, b) -> bool:
    """`None` y `''` son la misma celda vacía; al releer un libro openpyxl las iguala."""
    if a in (None, "") and b in (None, ""):
        return True
    return a == b


def _texto(valor_celda) -> str:
    if valor_celda is None:
        return ""
    if isinstance(valor_celda, float) and valor_celda.is_integer():
        return str(int(valor_celda))
    return str(valor_celda).strip()


def _fila(ws, fila: int) -> tuple:
    valores = []
    for columna in COLUMNAS_DATOS:
        celda = ws.cell(row=fila, column=columna)
        if columna in COLUMNAS_DINERO:
            valores.append(round(float(valor(ws, celda.coordinate) or 0), 2))
        else:
            valores.append(_texto(celda.value))
    return tuple(valores)


def leer_bloques(ws) -> list[Bloque]:
    """Divide la hoja en bloques: título, filas de datos y fila de total."""
    bloques: list[Bloque] = []
    titulo: str | None = None
    filas: list[tuple] = []
    for fila in range(5, ws.max_row + 1):
        texto_c = _texto(ws.cell(row=fila, column=3).value)
        texto_o = _texto(ws.cell(row=fila, column=15).value)
        tiene_datos = any(ws.cell(row=fila, column=c).value is not None for c in COLUMNAS_DATOS)

        if not tiene_datos:
            continue
        if texto_o.startswith("TOTAL"):
            bloques.append(
                Bloque(
                    titulo=titulo or "",
                    filas=tuple(filas),
                    total=(texto_o, *(_fila(ws, fila)[13:16])),
                )
            )
            titulo, filas = None, []
            continue
        if texto_c and not any(
            ws.cell(row=fila, column=c).value is not None for c in range(4, 21)
        ):
            if titulo is not None:
                bloques.append(Bloque(titulo=titulo, filas=tuple(filas), total=None))
                filas = []
            titulo = texto_c
            continue
        filas.append(_fila(ws, fila))

    if titulo is not None:
        bloques.append(Bloque(titulo=titulo, filas=tuple(filas), total=None))
    return bloques


def _periodo_del_titulo(titulo: str) -> Periodo | None:
    encontrado = re.search(r"DIAN\s+([A-Z]+)\s+(\d{4})", titulo)
    if not encontrado:
        return None
    return Periodo(anio=int(encontrado.group(2)), mes=MESES[encontrado.group(1)])


def _periodo_de_los_datos(ruta) -> Periodo:
    listado = LectorDianXlsx().leer(ruta)
    conteo = Counter((d.fecha_emision.year, d.fecha_emision.month) for d in listado.documentos)
    (anio, mes), _ = conteo.most_common(1)[0]
    return Periodo(anio=anio, mes=mes)


def cliente_y_periodo(ruta) -> tuple[Cliente, Periodo]:
    """Lee la cabecera del propio archivo; si está anonimizada, usa un cliente de prueba."""
    wb = load_workbook(ruta, data_only=True)
    try:
        ws = wb["Sumatorias"]
        nombre = _texto(ws["E1"].value)
        identificacion = _texto(ws["E2"].value)
        titulo = _texto(ws["E3"].value)
    finally:
        wb.close()

    periodo = _periodo_del_titulo(titulo) or _periodo_de_los_datos(ruta)

    digitos = re.search(r"\d[\d.]*", identificacion) if identificacion else None
    if digitos is None:
        # Referencias anonimizadas (D-23): no hay identificación real que buscar.
        cliente = Cliente(nombre=nombre or "REFERENCIA ANONIMIZADA", numero="1")
    else:
        tipo = "CC" if identificacion.upper().startswith("CC") else "NIT"
        digito = None
        if "-" in identificacion:
            digito = identificacion.rsplit("-", 1)[1].strip()
        cliente = Cliente(
            nombre=nombre,
            tipo_identificacion=tipo,
            numero=digitos.group(0).replace(".", ""),
            digito_verificacion=digito,
        )
    return cliente, periodo


def _procesar(ruta):
    cliente, periodo = cliente_y_periodo(ruta)
    return cliente, periodo, procesar_mes(ruta, cliente, periodo, LectorDianXlsx())


def _escribir(proceso, cliente, periodo, destino) -> None:
    """Escribe sin pasar por `exportar_hoja`, que aquí bloquearía por C6/C7 (D-23, D-24)."""
    EscritorOpenpyxl().escribir(
        proceso.resultado,
        cliente,
        periodo,
        destino,
        ruta_listado=proceso.ruta_listado,
    )


@pytest.fixture(scope="module")
def referencia(dir_referencias):
    ruta = dir_referencias / REFERENCIA_GOLDEN
    if not ruta.is_file():
        pytest.skip(f"Falta la referencia {REFERENCIA_GOLDEN}")
    return ruta


@pytest.fixture(scope="module")
def generado(referencia, tmp_path_factory):
    cliente, periodo, proceso = _procesar(referencia)
    destino = tmp_path_factory.mktemp("golden") / "generado.xlsx"
    _escribir(proceso, cliente, periodo, destino)
    return destino, referencia, proceso


# --- Datos y cuadres ----------------------------------------------------------------


def test_la_referencia_tiene_89_documentos(generado):
    _, _, proceso = generado
    assert proceso.filas_dian == 89
    assert proceso.total_dian == Decimal("36190379.92")
    assert len(proceso.resultado.documentos) == 89
    assert len(proceso.resultado.en_hoja) == 89
    assert proceso.resultado.excluidos == ()
    assert proceso.resultado.no_clasificados == ()


def test_cuadres_que_si_se_pueden_validar(generado):
    _, _, proceso = generado
    por_codigo = {c.codigo: c for c in proceso.cuadres}
    assert [c.codigo for c in proceso.cuadres] == ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    for codigo in ("C1", "C2", "C3", "C4", "C5"):
        assert por_codigo[codigo].ok, f"{codigo}: {por_codigo[codigo].detalle}"


def test_c6_falla_porque_la_referencia_esta_anonimizada(generado):
    _, _, proceso = generado
    c6 = next(c for c in proceso.cuadres if c.codigo == "C6")
    assert not c6.ok
    assert "no aparece en" in c6.detalle


def test_c7_marca_las_dos_facturas_con_otro_impuesto(generado):
    _, _, proceso = generado
    c7 = next(c for c in proceso.cuadres if c.codigo == "C7")
    assert not c7.ok
    assert "235797" in c7.detalle
    assert "35167450" in c7.detalle
    assert "(219.0)" in c7.detalle
    assert "(220.53)" in c7.detalle


def test_la_exportacion_se_bloquea_honestamente(generado):
    _, _, proceso = generado
    assert not proceso.puede_exportar
    assert {c.codigo for c in proceso.cuadres_fallidos} == {"C6", "C7"}


# --- Pestaña Dian -------------------------------------------------------------------


def test_pestanas(generado):
    ruta, _, _ = generado
    nuestro = load_workbook(ruta, data_only=False)
    try:
        assert nuestro.sheetnames == ["Dian", "Sumatorias", "Ventas", "Compras"]
    finally:
        nuestro.close()


def test_dian_es_copia_exacta(generado):
    ruta, referencia, _ = generado
    nuestro = load_workbook(ruta, data_only=True)
    original = load_workbook(referencia, data_only=True)
    try:
        a, b = nuestro["Dian"], original["Dian"]
        assert _referencia_filtro(a.auto_filter.ref) == _referencia_filtro(b.auto_filter.ref)
        assert a.freeze_panes == b.freeze_panes
        assert a.max_row == b.max_row
        for fila in range(1, b.max_row + 1):
            for columna in range(1, 33):
                assert _mismo_valor(
                    a.cell(row=fila, column=columna).value,
                    b.cell(row=fila, column=columna).value,
                ), f"difiere {a.cell(row=fila, column=columna).coordinate}"
    finally:
        nuestro.close()
        original.close()


# --- Estructura de las hojas de trabajo ---------------------------------------------


@pytest.mark.parametrize("hoja", ["Sumatorias", "Ventas", "Compras"])
def test_estructura_de_la_hoja(generado, hoja):
    ruta, referencia, _ = generado
    nuestro = load_workbook(ruta, data_only=False)
    original = load_workbook(referencia, data_only=True)
    try:
        a, b = nuestro[hoja], original[hoja]
        assert a["E1"].value == b["E1"].value
        assert a["E2"].value == b["E2"].value
        assert a["E3"].value == b["E3"].value
        assert {str(m) for m in a.merged_cells.ranges} == {
            str(m) for m in b.merged_cells.ranges
        }
        assert [a.cell(row=4, column=c).value for c in COLUMNAS_DATOS] == [
            b.cell(row=4, column=c).value for c in COLUMNAS_DATOS
        ]
        assert a.freeze_panes == b.freeze_panes == "A5"
        assert (
            _referencia_filtro(a.auto_filter.ref).split(":")[0]
            == _referencia_filtro(b.auto_filter.ref).split(":")[0]
        )

        bloques_nuestros = leer_bloques(a)
        bloques_reales = leer_bloques(b)
        assert [x.titulo for x in bloques_nuestros] == [x.titulo for x in bloques_reales]

        for nuestro_bloque, real in zip(bloques_nuestros, bloques_reales):
            assert sorted(nuestro_bloque.filas) == sorted(real.filas), (
                f"los documentos de {real.titulo!r} no coinciden"
            )
            assert nuestro_bloque.total == real.total, f"el total de {real.titulo!r} no coincide"
    finally:
        nuestro.close()
        original.close()


def test_suma_de_los_totales_del_mes(generado):
    ruta, _, _ = generado
    wb = load_workbook(ruta, data_only=False)
    try:
        ws = wb["Sumatorias"]
        totales = {}
        for fila in range(5, ws.max_row + 1):
            etiqueta = ws.cell(row=fila, column=15).value
            if isinstance(etiqueta, str) and etiqueta.strip().startswith("TOTAL"):
                totales[etiqueta.strip()] = round(valor(ws, f"R{fila}"), 2)
    finally:
        wb.close()

    # AGENTS.md §5: 89 documentos y 36.190.379,92 en total.
    assert set(totales) == {
        "TOTAL FACTURAS VENTAS",
        "TOTAL FACTURAS DE COMPRAS",
        "TOTAL DEVOLUCIONES EN COMPRAS",
        "TOTAL NOMINA",
    }
    assert round(sum(totales.values()), 2) == 36190379.92


# --- Las tres referencias -----------------------------------------------------------


@pytest.mark.parametrize("nombre", REFERENCIAS)
def test_las_tres_referencias_procesan_y_escriben(dir_referencias, nombre, tmp_path):
    ruta = dir_referencias / nombre
    if not ruta.is_file():
        pytest.skip(f"Falta {nombre}")

    cliente, periodo, proceso = _procesar(ruta)
    assert len(proceso.resultado.documentos) == proceso.filas_dian

    # C1..C5 deben pasar en las tres. C6 no se puede validar porque los NIT están
    # anonimizados (D-23); C7 solo falla en la referencia que trae INC real (D-24).
    fallidos = {c.codigo for c in proceso.cuadres_fallidos}
    assert fallidos - {"C6", "C7"} == set()
    assert "C6" in fallidos
    if nombre != REFERENCIA_GOLDEN:
        assert "C7" not in fallidos

    salida = tmp_path / "salida.xlsx"
    _escribir(proceso, cliente, periodo, salida)
    wb = load_workbook(salida, data_only=False)
    try:
        assert wb.sheetnames == ["Dian", "Sumatorias", "Ventas", "Compras"]
        assert wb["Dian"].max_row >= proceso.filas_dian + 1
    finally:
        wb.close()
