"""Caso de uso: aplicar las decisiones del usuario sobre las sugerencias de retención."""

from __future__ import annotations

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
            confirmadas.append(linea)
            continue
        concepto = decisiones.get(linea.documento.indice, linea.concepto)
        definicion = configuracion.conceptos.get(concepto)
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
            )
        )
    return retefuente_mes(confirmadas)
