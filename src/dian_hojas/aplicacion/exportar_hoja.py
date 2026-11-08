"""Caso de uso: exportar la hoja de trabajo con el nombre estándar.

La exportación se bloquea si algún cuadre falla o si el mes quedó sin documentos (D-17). Es
preferible un mensaje claro a un archivo que después parece un mes trabajado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Collection

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


class ConfirmacionRequerida(ExportacionBloqueada):
    """Hay alerta de otros impuestos (C7) y el usuario aún no confirmó (D-47)."""


def _sin_colision(destino: Path, ruta_listado: Path) -> Path:
    """Si la salida existe, agrega `_v2`, `_v3`, … en vez de sobrescribirla (D-51).

    Nunca devuelve la ruta del listado de entrada.
    """
    if destino.resolve() == ruta_listado.resolve():
        # El escritor ya lanza en ese caso; aquí se evita incluso el sufijo.
        return destino
    if not destino.exists():
        return destino
    base = destino.with_suffix("")
    sufijo = destino.suffix
    version = 2
    while True:
        candidato = base.with_name(f"{base.name}_v{version}{sufijo}")
        if not candidato.exists() and candidato.resolve() != ruta_listado.resolve():
            return candidato
        version += 1


def exportar_hoja(
    proceso: ResultadoProcesamiento,
    cliente: Cliente,
    periodo: Periodo,
    carpeta: Path,
    escritor: EscritorHoja,
    *,
    retefuente: RetefuenteMes | None = None,
    soportes_verificados: Collection[str] | None = None,
    confirmar_otros_impuestos: bool = False,
    confirmar_pendientes: bool = False,
) -> Path:
    """Genera el archivo en `carpeta` y devuelve su ruta.

    `retefuente` es el resultado del motor de retención (Fase 3); si viene con líneas, la pestaña
    `Retefuente [Mes]` se escribe después de `Compras`.

    `soportes_verificados` son los CUFEs cuyo soporte físico el usuario ya cruzó (Fase 4, opcional);
    solo marcan `FISICA = TRUE`, nunca bloquean la exportación.

    `confirmar_otros_impuestos` debe ser `True` cuando C7 está en alerta (otros
    impuestos distintos de IVA, D-47). Sin esa confirmación se lanza
    `ConfirmacionRequerida` y no se escribe ningún archivo.
    """
    if proceso.mes_vacio:
        raise MesVacio(
            "El listado del mes no tiene documentos: no se genera archivo. "
            "Revisa que hayas descargado el periodo correcto."
        )
    if proceso.cuadres_fallidos:
        raise CuadreFallido(proceso.cuadres_fallidos)
    if proceso.requiere_confirmacion_otros and not confirmar_otros_impuestos:
        detalle = "; ".join(f"{c.codigo}: {c.detalle}" for c in proceso.alertas)
        raise ConfirmacionRequerida(
            f"Hay impuestos distintos de IVA y debes confirmar antes de exportar: {detalle}. "
            "Marca «Entiendo la diferencia y quiero exportar»."
        )
    if retefuente is not None and retefuente.hay_pendientes and not confirmar_pendientes:
        raise ConfirmacionRequerida(
            f"Hay {retefuente.cantidad_pendientes} línea(s) de retención pendientes de confirmar. "
            "Confirma las retenciones o autoriza exportar como PROVISIONAL."
        )

    destino = Path(carpeta) / periodo.nombre_archivo(cliente)
    destino = _sin_colision(destino, Path(proceso.ruta_listado))
    return escritor.escribir(
        proceso.resultado,
        cliente,
        periodo,
        destino,
        ruta_listado=proceso.ruta_listado,
        retefuente=retefuente,
        soportes_verificados=soportes_verificados,
        otros_confirmados=bool(proceso.requiere_confirmacion_otros and confirmar_otros_impuestos),
    )
