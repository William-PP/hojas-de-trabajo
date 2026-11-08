"""Motor de retención en la fuente: puro, sin pandas, openpyxl, PySide6 ni sqlite3."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from dian_hojas.dominio.modelos import DocumentoElectronico

CERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class LineaRetefuente:
    """Una línea de retención sobre una compra: concepto, base, tarifa y resultado."""

    documento: DocumentoElectronico | None
    concepto: str
    base: Decimal
    base_minima_uvt: Decimal
    tarifa: Decimal
    supera_base: bool
    retencion: Decimal
    confirmada: bool = False

    @classmethod
    def crear(
        cls,
        documento: DocumentoElectronico | None,
        concepto: str,
        base: Decimal,
        base_minima_uvt: Decimal,
        tarifa: Decimal,
        uvt: Decimal,
        confirmada: bool = False,
    ) -> "LineaRetefuente":
        # TODO (D-49): ¿la base mínima se compara con >= o >? Confirmar con el contador.
        # Hoy es >=: base == base_minima_uvt * uvt ya supera. No cambiar sin esa confirmación.
        supera_base = base >= base_minima_uvt * uvt
        return cls(
            documento=documento,
            concepto=concepto,
            base=base,
            base_minima_uvt=base_minima_uvt,
            tarifa=tarifa,
            supera_base=supera_base,
            retencion=base * tarifa if supera_base else CERO,
            confirmada=confirmada,
        )


@dataclass(frozen=True, slots=True)
class RetefuenteMes:
    """El resultado del cálculo de retención para un mes."""

    lineas: tuple[LineaRetefuente, ...]
    total_retencion: Decimal
    anio: int | None = None
    uvt_pesos: Decimal | None = None
    conceptos: tuple[tuple[str, Decimal, Decimal], ...] = ()

    @property
    def pendientes(self) -> tuple[LineaRetefuente, ...]:
        return tuple(l for l in self.lineas if not l.confirmada)

    @property
    def hay_pendientes(self) -> bool:
        return any(not l.confirmada for l in self.lineas)

    @property
    def cantidad_pendientes(self) -> int:
        return len(self.pendientes)


def crear_linea(
    documento: DocumentoElectronico | None,
    concepto: str,
    base: Decimal,
    base_minima_uvt: Decimal,
    tarifa: Decimal,
    uvt: Decimal,
) -> LineaRetefuente:
    """Retención = base * tarifa si base supera la base mínima (base_minima_uvt × UVT); en caso contrario 0."""
    return LineaRetefuente.crear(documento, concepto, base, base_minima_uvt, tarifa, uvt)


def retener(base: Decimal, tarifa: Decimal, base_minima_uvt: Decimal, uvt: Decimal) -> Decimal:
    """Retención de una base frente a la mínima del concepto, con la UVT del año."""
    return crear_linea(None, "compras", base, base_minima_uvt, tarifa, uvt).retencion


def total_retencion(lineas: Iterable[LineaRetefuente]) -> Decimal:
    """Suma de retenciones de las líneas calculadas."""
    return sum((linea.retencion for linea in lineas), CERO)


def retefuente_mes(
    lineas: Iterable[LineaRetefuente],
    *,
    anio: int | None = None,
    uvt_pesos: Decimal | None = None,
    conceptos: tuple[tuple[str, Decimal, Decimal], ...] = (),
) -> RetefuenteMes:
    """Resultado del mes: líneas y retención total a declarar."""
    lineas_finales = tuple(lineas)
    return RetefuenteMes(
        lineas=lineas_finales,
        total_retencion=total_retencion(lineas_finales),
        anio=anio,
        uvt_pesos=uvt_pesos,
        conceptos=conceptos,
    )
