"""Pruebas de los artefactos de empaquetado (Fase 4)."""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_existe_el_especificador_de_pyinstaller() -> None:
    spec = RAIZ / "dian_hojas.spec"
    texto = spec.read_text(encoding="utf-8")

    assert spec.is_file()
    assert "HojasTrabajoDIAN" in texto
    assert "__main__.py" in texto


def test_existe_el_punto_de_entrada_ejecutable() -> None:
    entrada = RAIZ / "src" / "dian_hojas" / "__main__.py"
    assert entrada.is_file()
    assert "interfaz.main" in entrada.read_text(encoding="utf-8")


def test_existe_el_script_de_construccion() -> None:
    script = RAIZ / "scripts" / "construir_exe.ps1"
    texto = script.read_text(encoding="utf-8")

    assert script.is_file()
    assert "dian_hojas.spec" in texto
    assert "reglas" in texto
