"""Adaptador de lectura del archivo YAML de configuración tributaria por año."""

from __future__ import annotations

from pathlib import Path

from dian_hojas.reglas.configuracion import ConfiguracionTributaria, cargar_configuracion


class ConfigYaml:
    """Puerto de configuración tributaria: lee `reglas/[año].yaml`."""

    def __init__(self, directorio_reglas: Path) -> None:
        self.directorio_reglas = Path(directorio_reglas)

    def configuracion(self, anio: int) -> ConfiguracionTributaria:
        return cargar_configuracion(anio, self.directorio_reglas / f"{anio}.yaml")
