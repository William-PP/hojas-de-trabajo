"""Caso de uso: aplicar las decisiones del usuario sobre las sugerencias de retención."""

from __future__ import annotations

from decimal import Decimal

from dian_hojas.aplicacion.sugerir_retefuente import _es_excepcion
from dian_hojas.dominio.retefuente import LineaRetefuente, retefuente_mes
from dian_hojas.dominio.modelos import DocumentoElectronico
from dian_hojas.reglas.configuracion import ConfiguracionTributaria


def confirmar_retefuente(
    lineas: tuple[LineaRetefuente, ...],
    configuracion: ConfiguracionTributaria,
    decisiones: dict[int, str],
) -> RetefuenteMes:
    """Reaplica las decisiones del usuario (documento índice → concepto) sobre las sugerencias.

    La app sugiere y el usuario decide (regla 5 de `AGENTS.md`): sin decisión explícita la línea
    queda con el concepto sugerido; con decisión explícita se usa ese concepto.
    """
    confirmadas: list[LineaRetefuente] = []
    for linea in lineas:
        if linea.documento is None:
            confirmadas.append(
                LineaRetefuente(
                    documento=linea.documento,
                    concepto=linea.concepto,
                    base=linea.base,
                    base_minima_uvt=linea.base_minima_uvt,
                    tarifa=linea.tarifa,
                    supera_base=linea.supera_base,
                    retencion=linea.retencion,
                    confirmada=True,
                )
            )
            continue
        concepto = decisiones.get(linea.documento.indice, linea.concepto)
        if _es_excepcion(concepto):
            confirmadas.append(
                LineaRetefuente.crear(
                    linea.documento,
                    concepto,
                    linea.base,
                    Decimal("0"),
                    Decimal("0"),
                    configuracion.uvt_pesos,
                    confirmada=True,
                )
            )
            continue
        clave = concepto.strip().lower()
        definicion = next(
            (v for k, v in configuracion.conceptos.items() if k.strip().lower() == clave),
            None,
        )
        if definicion is None:
            raise ValueError(f"Falta el concepto {concepto!r} en la configuración tributaria.")
        confirmadas.append(
            LineaRetefuente.crear(
                linea.documento,
                concepto,
                linea.base,
                definicion.base_minima_uvt,
                definicion.tarifa,
                configuracion.uvt_pesos,
                confirmada=True,
            )
        )
    parametros = tuple(
        sorted(
            (nombre, dato.base_minima_uvt, dato.tarifa)
            for nombre, dato in configuracion.conceptos.items()
        )
    )
    return retefuente_mes(
        confirmadas,
        anio=configuracion.anio,
        uvt_pesos=configuracion.uvt_pesos,
        conceptos=parametros,
        fuente=getattr(configuracion, "fuente", "") or "",
        fecha_validacion=getattr(configuracion, "fecha_validacion", "") or "",
    )
