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


@pytest.fixture(scope="session")
def ruta_listado_sintetico(tmp_path_factory) -> Path:
    """Listado DIAN sintético, generado en memoria y guardado fuera del repositorio."""
    from tests.herramientas.listado_sintetico import crear_listado

    return crear_listado(tmp_path_factory.mktemp("listado") / "listado_sintetico.xlsx")


@pytest.fixture(scope="session")
def listado_sintetico(ruta_listado_sintetico: Path):
    """El listado sintético ya leído."""
    from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx

    return LectorDianXlsx().leer(ruta_listado_sintetico)


def pytest_collection_modifyitems(config, items):
    """Salta las pruebas que dependen de Referencias/ cuando la carpeta no existe."""
    if REFERENCIAS.is_dir():
        return
    motivo = "Requiere la carpeta Referencias/ (no versionada)"
    for item in items:
        if "referencias" in item.keywords:
            item.add_marker(pytest.mark.skip(reason=motivo))
