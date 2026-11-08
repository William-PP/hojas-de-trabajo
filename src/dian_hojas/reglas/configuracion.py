"""Configuración tributaria por año: UVT, conceptos, bases mínimas y tarifas.

El YAML lo provee el usuario (`reglas/[año].yaml`). El código nunca inventa ni completa valores
(regla 4 de `AGENTS.md`); si falta un dato se falla con un mensaje claro.

La Fase 4 agrega la escritura del mismo archivo desde la interfaz: `guardar_configuracion` valida lo
que el usuario escribió y lo serializa, sin rellenar valores por su cuenta.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping

import yaml

CERO = Decimal("0")
UNO = Decimal("1")
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
    fuente: str = ""
    fecha_validacion: str = ""


def _decimal(
    valor: object,
    *,
    campo: str,
    anio: int,
    origen: Path | None = None,
) -> Decimal:
    """Convierte a `Decimal` con mensajes que dicen exactamente qué dato falta o está mal."""
    donde = f" en {origen}" if origen is not None else ""
    if valor is None:
        raise ErrorConfiguracion(
            f"Falta el dato del año {anio}: '{campo}' no está{donde}."
        )
    texto = str(valor).strip()
    if not texto:
        raise ErrorConfiguracion(
            f"El dato del año {anio} '{campo}' está vacío{donde}."
        )
    try:
        return Decimal(texto)
    except (InvalidOperation, ValueError) as exc:
        raise ErrorConfiguracion(
            f"El dato del año {anio} '{campo}' no es un número válido: {texto!r}{donde}."
        ) from exc


def construir_configuracion(
    anio: int,
    uvt_pesos: object,
    conceptos: Mapping[str, object] | None,
    *,
    origen: Path | None = None,
    fuente: object = "",
    fecha_validacion: object = "",
) -> ConfiguracionTributaria:
    """Valida los datos y construye la configuración. No escribe nada."""
    anio = int(anio)
    uvt = _decimal(uvt_pesos, campo="uvt_pesos", anio=anio, origen=origen)
    if uvt <= CERO:
        raise ErrorConfiguracion(
            f"El dato del año {anio} 'uvt_pesos' debe ser mayor que cero."
        )

    if not isinstance(conceptos, Mapping):
        raise ErrorConfiguracion(
            f"Falta el dato del año {anio}: 'conceptos' no está"
            f"{f' en {origen}' if origen is not None else ''}."
        )

    validos: dict[str, ConceptoTributario] = {}
    faltantes: list[str] = []
    # Los cinco base son obligatorios; cualquier concepto extra que venga también se valida
    # y se conserva (D-49: el editor permite agregar conceptos nuevos).
    nombres_a_revisar: list[str] = list(CONCEPTOS)
    for clave in conceptos.keys():
        if clave not in nombres_a_revisar:
            nombres_a_revisar.append(clave)
    for nombre in nombres_a_revisar:
        dato = conceptos.get(nombre)
        if isinstance(dato, ConceptoTributario):
            base = dato.base_minima_uvt
            tarifa = dato.tarifa
        elif isinstance(dato, Mapping):
            base_bruto = dato.get("base_minima_uvt")
            tarifa_bruta = dato.get("tarifa")
            if (
                base_bruto is None
                or tarifa_bruta is None
                or not str(base_bruto).strip()
                or not str(tarifa_bruta).strip()
            ):
                faltantes.append(nombre)
                continue
            base = _decimal(
                base_bruto,
                campo=f"conceptos.{nombre}.base_minima_uvt",
                anio=anio,
                origen=origen,
            )
            tarifa = _decimal(
                tarifa_bruta,
                campo=f"conceptos.{nombre}.tarifa",
                anio=anio,
                origen=origen,
            )
        else:
            faltantes.append(nombre)
            continue

        if base < CERO:
            raise ErrorConfiguracion(
                f"El dato del año {anio} 'conceptos.{nombre}.base_minima_uvt' no puede ser negativo."
            )
        if tarifa < CERO or tarifa > UNO:
            raise ErrorConfiguracion(
                f"El dato del año {anio} 'conceptos.{nombre}.tarifa' debe estar entre 0 y 1 "
                f"(por ejemplo 0.05 para 5%); llegó {tarifa}."
            )
        validos[nombre] = ConceptoTributario(base_minima_uvt=base, tarifa=tarifa)

    if faltantes:
        raise ErrorConfiguracion(
            f"Faltan conceptos en la configuración del año {anio}: {', '.join(faltantes)}. "
            "Rellena base_minima_uvt y tarifa para cada concepto."
        )

    fuente_txt = "" if fuente is None else str(fuente).strip()
    fecha_txt = "" if fecha_validacion is None else str(fecha_validacion).strip()

    return ConfiguracionTributaria(anio=anio, uvt_pesos=uvt, conceptos=validos, fuente=fuente_txt, fecha_validacion=fecha_txt)


def texto_configuracion(configuracion: ConfiguracionTributaria) -> str:
    """Serializa la configuración con la misma forma que espera `cargar_configuracion`."""
    orden = [n for n in CONCEPTOS if n in configuracion.conceptos] + sorted(
        n for n in configuracion.conceptos if n not in CONCEPTOS
    )
    datos: dict[str, object] = {
        "anio": configuracion.anio,
        "uvt_pesos": str(configuracion.uvt_pesos),
        "fuente": str(configuracion.fuente),
        "fecha_validacion": str(configuracion.fecha_validacion),
        "conceptos": {
            nombre: {
                "base_minima_uvt": str(configuracion.conceptos[nombre].base_minima_uvt),
                "tarifa": str(configuracion.conceptos[nombre].tarifa),
            }
            for nombre in orden
        },
    }
    return yaml.safe_dump(datos, allow_unicode=True, sort_keys=False)


def guardar_configuracion(
    anio: int,
    ruta: Path,
    *,
    uvt_pesos: object,
    conceptos: Mapping[str, object] | None,
    fuente: object = "",
    fecha_validacion: object = "",
) -> Path:
    """Valida y escribe `reglas/[año].yaml`. Devuelve la ruta escrita."""
    ruta = Path(ruta)
    configuracion = construir_configuracion(anio, uvt_pesos, conceptos, origen=ruta, fuente=fuente, fecha_validacion=fecha_validacion)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto_configuracion(configuracion), encoding="utf-8")
    return ruta


def cargar_configuracion(anio: int, ruta: Path) -> ConfiguracionTributaria:
    """Lee `reglas/[año].yaml` y valida que no falte información sustantiva."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorConfiguracion(f"No existe la configuración tributaria para el año {anio}: {ruta}")

    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ErrorConfiguracion(f"La configuración tributaria del año {anio} no es un mapeo: {ruta}")

    return construir_configuracion(
        anio,
        datos.get("uvt_pesos"),
        datos.get("conceptos"),
        origen=ruta,
        fuente=datos.get("fuente", "") or "",
        fecha_validacion=datos.get("fecha_validacion", "") or "",
    )


def cargar_desde_archivo(ruta: Path, anio_por_defecto: int | None = None) -> ConfiguracionTributaria:
    """Carga un YAML existente usando el año que trae dentro (útil para «Cargar YAML»).

    Si el archivo no trae `anio`, se usa `anio_por_defecto`; si tampoco hay, se falla con un
    mensaje claro en vez de adivinar.
    """
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorConfiguracion(f"No existe el archivo de configuración: {ruta}")

    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ErrorConfiguracion(f"La configuración no es un mapeo: {ruta}")

    anio = datos.get("anio", anio_por_defecto)
    if anio is None:
        raise ErrorConfiguracion(
            f"El archivo {ruta} no dice a qué año corresponde. Elige el año en la ventana."
        )
    try:
        anio = int(anio)
    except (TypeError, ValueError) as exc:
        raise ErrorConfiguracion(f"El año del archivo {ruta} no es válido: {anio!r}") from exc

    return construir_configuracion(
        anio,
        datos.get("uvt_pesos"),
        datos.get("conceptos"),
        origen=ruta,
        fuente=datos.get("fuente", "") or "",
        fecha_validacion=datos.get("fecha_validacion", "") or "",
    )
