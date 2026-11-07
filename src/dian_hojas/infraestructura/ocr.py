"""Adaptador **opcional** de OCR para soportes físicos (PDF o imagen).

La aplicación no lo necesita para funcionar: si el usuario no aporta soportes, nada de esto se
ejecuta. Las dependencias (`pytesseract` + motor Tesseract, y `pdf2image` + poppler para PDF) se
instalan aparte con el extra `ocr` del proyecto.

Si faltan las dependencias, el archivo no existe o no tiene texto legible, se lanza `ErrorOcr` con
un mensaje claro: la interfaz lo muestra y sigue trabajando.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from dian_hojas.puertos import OcrProveedor


class ErrorOcr(RuntimeError):
    """No se pudo extraer texto del soporte físico."""


class Ocr(OcrProveedor):
    """Extrae texto de una imagen o PDF usando OCR (Tesseract).

    `motor` permite inyectar un extractor distinto en las pruebas; por defecto se usa Tesseract.
    """

    def __init__(self, motor: Callable[[Path], str] | None = None) -> None:
        self._motor = motor

    def extraer_texto(self, ruta: Path) -> str:
        ruta = Path(ruta)
        if not ruta.is_file():
            raise ErrorOcr(f"El soporte físico no existe: {ruta}")

        motor = self._motor or _motor_tesseract
        try:
            texto = motor(ruta)
        except ErrorOcr:
            raise
        except Exception as exc:  # pragma: no cover - depende del motor instalado
            raise ErrorOcr(f"No se pudo extraer texto de {ruta.name}: {exc}") from exc

        limpio = texto.strip()
        if not limpio:
            raise ErrorOcr(f"No se encontró texto legible en {ruta.name}.")
        return limpio


def _motor_tesseract(ruta: Path) -> str:
    """Motor real: importa las dependencias solo cuando se usa."""
    try:
        import pytesseract
    except ImportError as exc:
        raise ErrorOcr(
            "El OCR no está disponible: instala el extra 'ocr' "
            "(pytesseract y el motor Tesseract). La aplicación funciona sin él."
        ) from exc

    if ruta.suffix.lower() == ".pdf":
        try:
            from pdf2image import convert_from_path
        except ImportError as exc:
            raise ErrorOcr(
                "Para leer PDF con OCR instala 'pdf2image' y poppler, "
                "o entrega el soporte como imagen."
            ) from exc
        imagenes = convert_from_path(str(ruta))
        return "\n".join(pytesseract.image_to_string(imagen) for imagen in imagenes)

    return pytesseract.image_to_string(str(ruta))


def ocr_disponible() -> bool:
    """Indica si el motor de OCR está instalado, sin importarlo ni fallar."""
    from importlib.util import find_spec

    return find_spec("pytesseract") is not None
