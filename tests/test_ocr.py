"""Pruebas del adaptador OCR opcional (Fase 4).

El OCR nunca es obligatorio: la aplicación funciona sin él. Estas pruebas usan un motor inyectado
para no depender de Tesseract ni de poppler en el entorno.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dian_hojas.infraestructura.ocr import ErrorOcr, Ocr


def test_con_motor_inyectado_devuelve_el_texto_limpio(tmp_path: Path) -> None:
    soporte = tmp_path / "soporte.png"
    soporte.write_bytes(b"contenido")

    texto = Ocr(motor=lambda _ruta: "  Factura 123  ").extraer_texto(soporte)

    assert texto == "Factura 123"


def test_sin_texto_legible_falla(tmp_path: Path) -> None:
    soporte = tmp_path / "soporte.png"
    soporte.write_bytes(b"contenido")

    with pytest.raises(ErrorOcr, match="texto legible"):
        Ocr(motor=lambda _ruta: "   ").extraer_texto(soporte)


def test_archivo_inexistente_falla_antes_de_tocar_el_motor(tmp_path: Path) -> None:
    with pytest.raises(ErrorOcr, match="no existe"):
        Ocr(motor=lambda _ruta: "no deberia llamarse").extraer_texto(tmp_path / "no-existe.png")


def test_error_del_motor_se_envuelve_con_mensaje_claro(tmp_path: Path) -> None:
    soporte = tmp_path / "soporte.png"
    soporte.write_bytes(b"contenido")

    def motor_roto(_ruta: Path) -> str:
        raise RuntimeError("Tesseract no está instalado")

    with pytest.raises(ErrorOcr, match="Tesseract no está instalado"):
        Ocr(motor=motor_roto).extraer_texto(soporte)
