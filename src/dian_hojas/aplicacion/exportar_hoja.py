"""Caso de uso: exportar la hoja de trabajo con el nombre estándar.

La exportación se bloquea si algún cuadre falla o si el mes quedó sin documentos (D-17). Es
preferible un mensaje claro a un archivo que después parece un mes trabajado.
"""

from __future__ import annotations

from pathlib import Path

from dian_hojas.aplicacion.procesar_mes import ResultadoProcesamiento
from dian_hojas.dominio.modelos import Cliente, Periodo
from dian_hojas.dominio.retefuente import RetefuenteMes
from dian_hojas.puertos import EscritorHoja


class ExportacionBloqueada(RuntimeError):
    """No se puede exportar: el mes está vacío o algún cuadre falló."""


class MesVacio(ExportacionBloqueada):
    """El listado no trae documentos que llevar a las hojas."""


class CuadreFallido(ExportacionBloqueada):
    """Algún cuadre obligatorio falló."""

    def __init__(self, cuadres) -> None:
        self.cuadres = tuple(cuadres)
        detalle = "; ".join(f"{c.codigo} {c.titulo}: {c.detalle}" for c in self.cuadres)
        super().__init__(f"No se puede exportar, hay cuadres fallidos: {detalle}")


def exportar_hoja(
    proceso: ResultadoProcesamiento,
    cliente: Cliente,
    periodo: Periodo,
    carpeta: Path,
    escritor: EscritorHoja,
    *,
    retefuente: RetefuenteMes | None = None,
) -> Path:
    """Genera el archivo en `carpeta` y devuelve su ruta.

    `retefuente` es el resultado del motor de retención (Fase 3); si viene con líneas, la pestaña
    `Retefuente [Mes]` se escribe después de `Compras`.
    """
    if proceso.mes_vacio:
        raise MesVacio(
            "El listado del mes no tiene documentos: no se genera archivo. "
            "Revisa que hayas descargado el periodo correcto."
        )
    if proceso.cuadres_fallidos:
        raise CuadreFallido(proceso.cuadres_fallidos)

    destino = Path(carpeta) / periodo.nombre_archivo(cliente)
    return escritor.escribir(
        proceso.resultado,
        cliente,
        periodo,
        destino,
        ruta_listado=proceso.ruta_listado,
        retefuente=retefuente,
    )
