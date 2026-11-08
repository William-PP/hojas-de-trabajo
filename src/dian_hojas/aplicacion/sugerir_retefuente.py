"""Caso de uso: sugerir el concepto de retención de cada compra del mes."""

from __future__ import annotations

from decimal import Decimal

from dian_hojas.dominio.retefuente import LineaRetefuente, RetefuenteMes, retefuente_mes
from dian_hojas.dominio.modelos import DocumentoElectronico
from dian_hojas.puertos import RepositorioProveedores
from dian_hojas.reglas.configuracion import ConfiguracionTributaria, ErrorConfiguracion

CONCEPTO_DEFAULT = "compras"
EXCEPCIONES = {"no aplica", "no_aplica", "autorretenedor", "no sujeto", "no sujeto a retencion", "no sujeto a retención"}


def _es_excepcion(concepto: str) -> bool:
    return concepto.strip().lower() in EXCEPCIONES


def sugerir_retefuente(
    documentos_compras: tuple[DocumentoElectronico, ...],
    configuracion: ConfiguracionTributaria,
    repo: RepositorioProveedores,
) -> RetefuenteMes:
    """Sugiere el concepto y calcula la retención de cada compra.

    El concepto sugerido viene del repositorio (proveedor → concepto); si el proveedor no tiene
    decisión, se sugiere el concepto por defecto del año en la configuración. Toda línea nace
    **pendiente de confirmar** (`confirmada=False`, regla 5).

    Si el proveedor está marcado como excepción (`no aplica` / `autorretenedor`), la línea queda
    con tarifa 0 y sin retención, sin exigir entrada en la configuración.
    """
    lineas: list[LineaRetefuente] = []
    for documento in documentos_compras:
        concepto = repo.concepto_de_proveedor(documento.nit_emisor) or CONCEPTO_DEFAULT
        if _es_excepcion(concepto):
            linea = LineaRetefuente.crear(
                documento,
                concepto,
                documento.total_neto,
                Decimal("0"),
                Decimal("0"),
                configuracion.uvt_pesos,
                confirmada=False,
            )
            lineas.append(linea)
            continue
        # Conceptos nuevos y existentes se resuelven igual: clave normalizada a minúsculas.
        clave = concepto.strip().lower()
        definicion = next(
            (v for k, v in configuracion.conceptos.items() if k.strip().lower() == clave),
            None,
        )
        if definicion is None:
            raise ErrorConfiguracion(
                f"Falta el concepto {concepto!r} en la configuración tributaria del año "
                f"{configuracion.anio}: falta base_minima_uvt y/o tarifa."
            )
        linea = LineaRetefuente.crear(
            documento,
            concepto,
            documento.total_neto,
            definicion.base_minima_uvt,
            definicion.tarifa,
            configuracion.uvt_pesos,
            confirmada=False,
        )
        lineas.append(linea)
    parametros = tuple(
        sorted(
            (nombre, dato.base_minima_uvt, dato.tarifa)
            for nombre, dato in configuracion.conceptos.items()
        )
    )
    return retefuente_mes(
        lineas,
        anio=configuracion.anio,
        uvt_pesos=configuracion.uvt_pesos,
        conceptos=parametros,
        fuente=getattr(configuracion, "fuente", "") or "",
        fecha_validacion=getattr(configuracion, "fecha_validacion", "") or "",
    )
