"""Caso de uso: sugerir el concepto de retención de cada compra del mes."""

from __future__ import annotations

from dian_hojas.dominio.retefuente import LineaRetefuente, RetefuenteMes, retefuente_mes
from dian_hojas.dominio.modelos import DocumentoElectronico
from dian_hojas.puertos import RepositorioProveedores
from dian_hojas.reglas.configuracion import ConfiguracionTributaria, ErrorConfiguracion

CONCEPTO_DEFAULT = "compras"


def sugerir_retefuente(
    documentos_compras: tuple[DocumentoElectronico, ...],
    configuracion: ConfiguracionTributaria,
    repo: RepositorioProveedores,
) -> RetefuenteMes:
    """Sugiere el concepto y calcula la retención de cada compra.

    El concepto sugerido viene del repositorio (proveedor → concepto); si el proveedor no tiene
    decisión, se sugiere el concepto por defecto del año en la configuración.
    """
    lineas: list[LineaRetefuente] = []
    for documento in documentos_compras:
        concepto = repo.concepto_de_proveedor(documento.nit_emisor) or CONCEPTO_DEFAULT
        definicion = configuracion.conceptos.get(concepto)
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
        )
        lineas.append(linea)
    return retefuente_mes(lineas)
