"""Pruebas del motor de retención, la configuración tributaria y la pestaña `Retefuente`.

Fase 3. Las tarifas y bases mínimas salen siempre del YAML (D-18/D-24); aquí se usan valores
sintéticos para probar el motor sin tocar los datos reales.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook

from dian_hojas.aplicacion.confirmar_retefuente import confirmar_retefuente
from dian_hojas.aplicacion.exportar_hoja import exportar_hoja
from dian_hojas.aplicacion.procesar_mes import procesar_mes
from dian_hojas.aplicacion.sugerir_retefuente import sugerir_retefuente
from dian_hojas.dominio.retefuente import LineaRetefuente, retener, retefuente_mes
from dian_hojas.dominio.modelos import Categoria, Cliente, Periodo
from dian_hojas.infraestructura.config_yaml import ConfigYaml
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl
from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx
from dian_hojas.infraestructura.repo_sqlite import RepoSqlite
from dian_hojas.reglas.configuracion import (
    CONCEPTOS,
    ConceptoTributario,
    ConfiguracionTributaria,
    ErrorConfiguracion,
    cargar_configuracion,
)
from tests.herramientas.documentos import documento

CLIENTE = Cliente(nombre="Cliente Sintetico SAS", numero="1020396459")
PERIODO = Periodo(anio=2026, mes=10)


def _yaml(tmp_path: Path, anio: int = 2026, uvt: object = 220000, conceptos: object = None) -> Path:
    conceptos = conceptos or {
        nombre: {"base_minima_uvt": 1, "tarifa": 0.05} for nombre in CONCEPTOS
    }
    cuerpo = f"anio: {anio}\nuvt_pesos: {uvt}\nconceptos:\n"
    for nombre, dato in conceptos.items():
        base_minima = dato.get("base_minima_uvt") if isinstance(dato, dict) else dato
        tarifa = dato.get("tarifa") if isinstance(dato, dict) else None
        cuerpo += f"  {nombre}:\n    base_minima_uvt: {base_minima}\n    tarifa: {tarifa if tarifa is not None else '~'}\n"
    ruta = tmp_path / f"reglas_{anio}.yaml"
    ruta.write_text(cuerpo, encoding="utf-8")
    return ruta


# --- Motor --------------------------------------------------------------------------


def test_retener_cuando_no_supera_la_base_minima():
    assert retener(Decimal("1000"), Decimal("0.05"), Decimal("100"), Decimal("220000")) == Decimal("0")
    assert retener(Decimal("1000000"), Decimal("0.05"), Decimal("1"), Decimal("220000")) == Decimal("50000")


def test_retefuente_mes_suma_las_retenciones():
    linea = LineaRetefuente.crear(documento(), "compras", Decimal("1000000"), Decimal("1"), Decimal("0.05"), Decimal("220000"))
    assert linea.supera_base is True
    assert linea.retencion == Decimal("50000")
    resultado = retefuente_mes((linea,))
    assert resultado.total_retencion == Decimal("50000")
    assert resultado.lineas == (linea,)


# --- Configuración tributaria ---------------------------------------------------------


def test_configuracion_tributaria_ok(tmp_path):
    ruta = _yaml(tmp_path)
    config = cargar_configuracion(2026, ruta)
    assert config.anio == 2026
    assert config.uvt_pesos == Decimal("220000")
    assert config.conceptos["compras"] == ConceptoTributario(base_minima_uvt=Decimal("1"), tarifa=Decimal("0.05"))


def test_configuracion_falla_sin_uvt(tmp_path):
    ruta = tmp_path / "2026.yaml"
    ruta.write_text("conceptos:\n  compras:\n    base_minima_uvt: 1\n    tarifa: 0.05\n", encoding="utf-8")
    with pytest.raises(ErrorConfiguracion, match="uvt_pesos"):
        cargar_configuracion(2026, ruta)


def test_configuracion_falla_con_conceptos_incompletos(tmp_path):
    ruta = _yaml(tmp_path, conceptos={nombre: {"base_minima_uvt": 1} for nombre in CONCEPTOS})
    with pytest.raises(ErrorConfiguracion, match="honorarios"):
        cargar_configuracion(2026, ruta)


# --- Sugerencia y confirmación de retención -------------------------------------------


def test_sugerir_retefuente_calcula_por_concepto(tmp_path):
    ruta_listado = tmp_path / "listado.xlsx"
    from tests.herramientas.listado_sintetico import crear_listado

    ruta_listado = crear_listado(tmp_path / "listado.xlsx")
    listado = LectorDianXlsx().leer(ruta_listado)
    compras = tuple(
        d for d in listado.documentos if d.categoria is Categoria.COMPRA
    )
    config = cargar_configuracion(2026, _yaml(tmp_path))
    repo = RepoSqlite(tmp_path / "proveedores.sqlite")

    sugerencia = sugerir_retefuente(compras, config, repo)
    assert sugerencia.lineas, "el listado sintético debe tener compras para retener"
    assert sugerencia.lineas[0].concepto == "compras"
    assert sugerencia.total_retencion == sum((l.retencion for l in sugerencia.lineas), Decimal("0"))


def test_confirmar_retefuente_reaplica_la_decision(tmp_path):
    linea = LineaRetefuente.crear(documento(), "compras", Decimal("1000000"), Decimal("1"), Decimal("0.05"), Decimal("220000"))
    lineas = (linea,)
    config = ConfiguracionTributaria(
        anio=2026,
        uvt_pesos=Decimal("220000"),
        conceptos={
            "compras": ConceptoTributario(base_minima_uvt=Decimal("1"), tarifa=Decimal("0.05")),
            "honorarios": ConceptoTributario(base_minima_uvt=Decimal("1"), tarifa=Decimal("0.11")),
        },
    )
    confirmadas = confirmar_retefuente(lineas, config, {0: "honorarios"})
    assert confirmadas.lineas[0].concepto == "honorarios"


# --- Exportación con retefuente -------------------------------------------------------


def test_exportar_hoja_escribe_la_pestaña_retefuente(tmp_path, ruta_listado_sintetico):
    proceso = procesar_mes(ruta_listado_sintetico, CLIENTE, PERIODO, LectorDianXlsx())
    assert proceso.puede_exportar
    retefuente = retefuente_mes(
        (
            LineaRetefuente.crear(
                next(d for d in proceso.resultado.documentos if d.categoria is Categoria.COMPRA),
                "compras",
                Decimal("1000000"),
                Decimal("1"),
                Decimal("0.05"),
                Decimal("220000"),
            ),
        )
    )
    salida = exportar_hoja(
        proceso,
        CLIENTE,
        PERIODO,
        tmp_path / "salida",
        EscritorOpenpyxl(),
        retefuente=retefuente,
    )
    wb = load_workbook(salida)
    try:
        assert "Retefuente Octubre" in wb.sheetnames
        ws = wb["Retefuente Octubre"]
        assert ws["U5"].value == "compras"
        assert ws["Z5"].value == 50000
        assert ws["U6"].value == "compras"
        assert ws["Z6"].value == 50000
        assert ws["U7"].value == "TOTAL RETENCIÓN A DECLARAR"
        assert ws["Z7"].value == 50000
    finally:
        wb.close()
