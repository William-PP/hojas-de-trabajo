"""Configuración tributaria por año: UVT, conceptos, bases mínimas y tarifas.

El YAML lo provee el usuario (`reglas/[año].yaml`). El código nunca inventa ni completa valores
(regla 4 de `AGENTS.md`); si falta un dato se falla con un mensaje claro.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml

CERO = Decimal("0")
CONCEPTOS = ("compras", "servicios", "honorarios", "arrendamientos", "transporte")


class ErrorConfiguracion(ValueError):
    """Falta o está mal la configuración tributaria del año."""


@dataclass(frozen=True, slots=True)
class ConceptoTributario:
    """Base mínima (en UVT) y tarifa de retención para un concepto."""

    base_minima_uvt: Decimal
    tarifa: Decimal


@dataclass(frozen=True, slots=True)
class ConfiguracionTributaria:
    """Todo lo que el motor de retención necesita del año en curso."""

    anio: int
    uvt_pesos: Decimal
    conceptos: dict[str, ConceptoTributario]


def cargar_configuracion(anio: int, ruta: Path) -> ConfiguracionTributaria:
    """Lee `reglas/[año].yaml` y valida que no falte información sustantiva."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorConfiguracion(f"No existe la configuración tributaria para el año {anio}: {ruta}")

    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ErrorConfiguracion(f"La configuración tributaria del año {anio} no es un mapeo: {ruta}")

    uvt = datos.get("uvt_pesos")
    if uvt is None:
        raise ErrorConfiguracion(f"Falta el dato del año {anio}: 'uvt_pesos' no está en {ruta}")
    uvt_pesos = Decimal(str(uvt))

    conceptos_datos = datos.get("conceptos")
    if not isinstance(conceptos_datos, dict):
        raise ErrorConfiguracion(f"Falta el dato del año {anio}: 'conceptos' no está en {ruta}")

    conceptos: dict[str, ConceptoTributario] = {}
    faltantes: list[str] = []
    for nombre in CONCEPTOS:
        dato = conceptos_datos.get(nombre)
        if (
            not isinstance(dato, dict)
            or dato.get("base_minima_uvt") is None
            or dato.get("tarifa") is None
        ):
            faltantes.append(nombre)
            continue
        conceptos[nombre] = ConceptoTributario(
            base_minima_uvt=Decimal(str(dato["base_minima_uvt"])),
            tarifa=Decimal(str(dato["tarifa"])),
        )
    if faltantes:
        raise ErrorConfiguracion(
            f"Faltan conceptos en {ruta}: {', '.join(faltantes)}. "
            "Rellena base_minima_uvt y tarifa para cada concepto."
        )

    return ConfiguracionTributaria(anio=anio, uvt_pesos=uvt_pesos, conceptos=conceptos)
