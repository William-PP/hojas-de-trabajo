"""Caso de uso: procesar el listado de un mes y dejar el resultado listo para revisar."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from dian_hojas.dominio.cuadres import ResultadoCuadre, ejecutar_cuadres, hay_cuadres_fallidos
from dian_hojas.dominio.modelos import Cliente, Periodo, ResultadoMes, construir_resultado
from dian_hojas.puertos import LectorListado


@dataclass(frozen=True, slots=True)
class ResultadoProcesamiento:
    """Todo lo que la interfaz necesita mostrar después de leer el archivo."""

    resultado: ResultadoMes
    cuadres: tuple[ResultadoCuadre, ...]
    ruta_listado: Path
    filas_dian: int
    total_dian: Decimal

    @property
    def mes_vacio(self) -> bool:
        """El listado no trajo ningún documento que pueda ir a las hojas (D-17)."""
        return not self.resultado.en_hoja

    @property
    def cuadres_fallidos(self) -> tuple[ResultadoCuadre, ...]:
        return tuple(c for c in self.cuadres if not c.ok and c.bloqueante)

    @property
    def alertas(self) -> tuple[ResultadoCuadre, ...]:
        """Cuadres que fallan pero no bloquean (C7 con otros impuestos, D-47)."""
        return tuple(c for c in self.cuadres if not c.ok and not c.bloqueante)

    @property
    def requiere_confirmacion_otros(self) -> bool:
        """Hay otros impuestos y el usuario debe confirmar antes de exportar."""
        return bool(self.alertas)

    @property
    def puede_exportar(self) -> bool:
        return not self.mes_vacio and not hay_cuadres_fallidos(self.cuadres)


def procesar_mes(
    ruta_listado: Path,
    cliente: Cliente,
    periodo: Periodo,
    lector: LectorListado,
) -> ResultadoProcesamiento:
    """Lee el listado, clasifica y ejecuta los cuadres. No escribe nada."""
    ruta_listado = Path(ruta_listado)
    listado = lector.leer(ruta_listado)
    resultado = construir_resultado(listado.documentos)
    cuadres = ejecutar_cuadres(
        resultado,
        cliente,
        periodo,
        filas_dian=listado.filas,
        total_dian=listado.total,
    )
    return ResultadoProcesamiento(
        resultado=resultado,
        cuadres=cuadres,
        ruta_listado=ruta_listado,
        filas_dian=listado.filas,
        total_dian=listado.total,
    )
