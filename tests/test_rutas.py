"""Pruebas de la resolución de carpetas de reglas y datos (fuente y ejecutable)."""

from __future__ import annotations

from pathlib import Path

from dian_hojas import rutas


def test_las_variables_de_entorno_mandan(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(rutas.VARIABLE_REGLAS, str(tmp_path / "mis-reglas"))
    monkeypatch.setenv(rutas.VARIABLE_DATOS, str(tmp_path / "mis-datos"))

    assert rutas.directorio_reglas() == tmp_path / "mis-reglas"
    assert rutas.directorio_datos() == tmp_path / "mis-datos"


def test_por_defecto_las_reglas_estan_en_el_repositorio(monkeypatch) -> None:
    monkeypatch.delenv(rutas.VARIABLE_REGLAS, raising=False)

    directorio = rutas.directorio_reglas()

    assert directorio.name == "reglas"
    assert (directorio / "README.md").is_file()


def test_los_datos_locales_van_al_home_del_usuario(monkeypatch) -> None:
    monkeypatch.delenv(rutas.VARIABLE_DATOS, raising=False)
    monkeypatch.delenv("DIAN_HOJAS_DATOS", raising=False)

    assert rutas.directorio_datos().name == ".dian_hojas"
