"""Configuración compartida de las pruebas."""

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
REFERENCIAS = RAIZ / "Referencias"


@pytest.fixture(scope="session")
def dir_fixtures() -> Path:
    """Carpeta con los archivos sintéticos o anonimizados que sí se versionan."""
    return FIXTURES


@pytest.fixture(scope="session")
def dir_referencias() -> Path:
    """Carpeta con los archivos reales del usuario. No está versionada."""
    return REFERENCIAS


def pytest_collection_modifyitems(config, items):
    """Salta las pruebas que dependen de Referencias/ cuando la carpeta no existe."""
    if REFERENCIAS.is_dir():
        return
    motivo = "Requiere la carpeta Referencias/ (no versionada)"
    for item in items:
        if "referencias" in item.keywords:
            item.add_marker(pytest.mark.skip(reason=motivo))
