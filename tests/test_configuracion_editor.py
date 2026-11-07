"""Pruebas del editor de configuración tributaria (guardar/cargar YAML).

El editor de la interfaz se apoya en estas funciones puras: no inventa valores, solo serializa lo
que el usuario escribe y valida que esté completo (regla 4 de `AGENTS.md`).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from dian_hojas.reglas.configuracion import (
    CONCEPTOS,
    ConceptoTributario,
    ErrorConfiguracion,
    cargar_configuracion,
    cargar_desde_archivo,
    guardar_configuracion,
)


def conceptos_ok() -> dict[str, ConceptoTributario]:
    return {nombre: ConceptoTributario(Decimal("1"), Decimal("0.05")) for nombre in CONCEPTOS}


def test_guardar_y_cargar_ida_y_vuelta(tmp_path: Path) -> None:
    ruta = guardar_configuracion(
        2026,
        tmp_path / "2026.yaml",
        uvt_pesos=Decimal("220000"),
        conceptos=conceptos_ok(),
    )

    configuracion = cargar_configuracion(2026, ruta)

    assert configuracion.anio == 2026
    assert configuracion.uvt_pesos == Decimal("220000")
    assert configuracion.conceptos["compras"].base_minima_uvt == Decimal("1")
    assert configuracion.conceptos["compras"].tarifa == Decimal("0.05")
    assert ruta.read_text(encoding="utf-8").startswith("anio: 2026")


def test_guardar_acepta_textos_de_la_interfaz(tmp_path: Path) -> None:
    ruta = guardar_configuracion(
        2026,
        tmp_path / "2026.yaml",
        uvt_pesos="230000.50",
        conceptos={nombre: {"base_minima_uvt": "2", "tarifa": "0.10"} for nombre in CONCEPTOS},
    )

    configuracion = cargar_configuracion(2026, ruta)
    assert configuracion.uvt_pesos == Decimal("230000.50")
    assert configuracion.conceptos["servicios"].tarifa == Decimal("0.10")


def test_cargar_desde_archivo_usa_el_anio_del_yaml(tmp_path: Path) -> None:
    ruta = guardar_configuracion(
        2027,
        tmp_path / "cualquiera.yaml",
        uvt_pesos="240000",
        conceptos=conceptos_ok(),
    )

    configuracion = cargar_desde_archivo(ruta)
    assert configuracion.anio == 2027


def test_falta_un_concepto(tmp_path: Path) -> None:
    incompletos = conceptos_ok()
    del incompletos["transporte"]
    with pytest.raises(ErrorConfiguracion, match="transporte"):
        guardar_configuracion(
            2026,
            tmp_path / "2026.yaml",
            uvt_pesos="220000",
            conceptos=incompletos,
        )
    assert not (tmp_path / "2026.yaml").exists()


@pytest.mark.parametrize("uvt", ["", "0", "-1", "no-es-numero"])
def test_uvt_invalida(tmp_path: Path, uvt: str) -> None:
    with pytest.raises(ErrorConfiguracion, match="uvt_pesos"):
        guardar_configuracion(
            2026,
            tmp_path / "2026.yaml",
            uvt_pesos=uvt,
            conceptos=conceptos_ok(),
        )


@pytest.mark.parametrize("tarifa", ["-0.01", "1.01", "no-es-numero"])
def test_tarifa_invalida(tmp_path: Path, tarifa: str) -> None:
    with pytest.raises(ErrorConfiguracion, match="tarifa"):
        guardar_configuracion(
            2026,
            tmp_path / "2026.yaml",
            uvt_pesos="220000",
            conceptos={
                nombre: {"base_minima_uvt": "1", "tarifa": tarifa}
                for nombre in CONCEPTOS
            },
        )
