"""Cuadres obligatorios del mes.

Funciones puras: no abren archivos, no lanzan excepciones, no formatean para la interfaz.
Cada cuadre devuelve un `ResultadoCuadre` con un detalle accionable.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from dian_hojas.dominio.modelos import Cliente, DocumentoElectronico, Periodo, ResultadoMes

TOLERANCIA = Decimal("0.01")
MAX_LISTADOS = 8

_SOLO_DIGITOS = re.compile(r"\D")


@dataclass(frozen=True, slots=True)
class ResultadoCuadre:
    codigo: str
    titulo: str
    ok: bool
    detalle: str
    bloqueante: bool = True


def _resumen(items: list[str]) -> str:
    if len(items) <= MAX_LISTADOS:
        return ", ".join(items)
    return ", ".join(items[:MAX_LISTADOS]) + f" y {len(items) - MAX_LISTADOS} más"


def _referencia(documento: DocumentoElectronico) -> str:
    folio = f"{documento.prefijo}-{documento.folio}" if documento.prefijo else documento.folio
    return f"{folio} ({documento.cufe[:8]}…)"


def _digitos(texto: str) -> str:
    return _SOLO_DIGITOS.sub("", texto or "").lstrip("0")


def _menciona(documento: DocumentoElectronico, cliente: Cliente) -> bool:
    buscado = _digitos(cliente.numero_digitos)
    if not buscado:
        return False
    return buscado in {_digitos(documento.nit_emisor), _digitos(documento.nit_receptor)}


def cuadre_cantidad(resultado: ResultadoMes, filas_dian: int) -> ResultadoCuadre:
    """C1: todo documento del listado llega a una hoja o queda justificado como excluido."""
    en_hoja = len(resultado.en_hoja)
    excluidos = len(resultado.excluidos)
    sin_clasificar = len(resultado.no_clasificados)
    contados = en_hoja + excluidos + sin_clasificar

    problemas: list[str] = []
    if sin_clasificar:
        problemas.append(
            f"{sin_clasificar} documento(s) sin clasificar: "
            + _resumen([_referencia(d) for d in resultado.no_clasificados])
        )
    if contados != filas_dian:
        problemas.append(f"entre las hojas hay {en_hoja} filas, {excluidos} excluidas y {filas_dian} en la DIAN")
    if len(resultado.documentos) != filas_dian:
        problemas.append(f"el listado trae {filas_dian} filas y se leyeron {len(resultado.documentos)}")

    return ResultadoCuadre(
        codigo="C1",
        titulo="Cantidad de documentos",
        ok=not problemas,
        detalle="; ".join(problemas) if problemas else f"{filas_dian} documentos, todos contados",
    )


def cuadre_total(resultado: ResultadoMes, total_dian: Decimal) -> ResultadoCuadre:
    """C2: la suma de los bloques coincide con la columna Total de la DIAN."""
    diferencia = resultado.total - total_dian
    ok = abs(diferencia) <= TOLERANCIA
    return ResultadoCuadre(
        codigo="C2",
        titulo="Total de los bloques contra la DIAN",
        ok=ok,
        detalle=(
            f"bloques {resultado.total} vs DIAN {total_dian}"
            + ("" if ok else f" (diferencia {diferencia})")
        ),
    )


def cuadre_cufe_unico(resultado: ResultadoMes) -> ResultadoCuadre:
    """C3: ningún CUFE se repite."""
    conteo = Counter(d.cufe for d in resultado.documentos if d.cufe)
    repetidos = sorted(cufe for cufe, veces in conteo.items() if veces > 1)
    return ResultadoCuadre(
        codigo="C3",
        titulo="CUFE único",
        ok=not repetidos,
        detalle=(
            "CUFE repetidos: " + _resumen(repetidos) if repetidos else "sin CUFE repetidos"
        ),
    )


def cuadre_bloques(resultado: ResultadoMes) -> ResultadoCuadre:
    """C4: Ventas + Compras (+ devoluciones y nómina) = Sumatorias, sin repetir documentos."""
    indices = [d.indice for d in resultado.en_hoja]
    repetidos = len(indices) - len(set(indices))
    suma_bloques = resultado.total
    suma_documentos = sum((d.total for d in resultado.en_hoja), Decimal("0"))
    diferencia = suma_bloques - suma_documentos
    sin_destino = len(resultado.documentos) - len(resultado.en_hoja) - len(resultado.excluidos)

    problemas: list[str] = []
    if repetidos:
        problemas.append(f"{repetidos} documento(s) en más de un bloque")
    if sin_destino:
        problemas.append(f"{sin_destino} documento(s) sin bloque asignado")
    if abs(diferencia) > TOLERANCIA:
        problemas.append(f"bloques {suma_bloques} vs documentos {suma_documentos}")

    return ResultadoCuadre(
        codigo="C4",
        titulo="Cuadre entre pestañas",
        ok=not problemas,
        detalle="; ".join(problemas) if problemas else "Ventas + Compras + devoluciones + nómina = Sumatorias",
    )


def cuadre_periodo(resultado: ResultadoMes, periodo: Periodo) -> ResultadoCuadre:
    """C5: todas las fechas de emisión pertenecen al mes y año."""
    fuera = [d for d in resultado.documentos if not periodo.contiene(d.fecha_emision)]
    return ResultadoCuadre(
        codigo="C5",
        titulo="Fechas dentro del periodo",
        ok=not fuera,
        detalle=(
            "fuera del periodo: "
            + _resumen([f"{_referencia(d)} {d.fecha_emision.isoformat()}" for d in fuera])
            if fuera
            else f"todas las fechas son de {periodo.nombre_mes} {periodo.anio}"
        ),
    )


def cuadre_cliente(resultado: ResultadoMes, cliente: Cliente) -> ResultadoCuadre:
    """C6: la identificación del cliente aparece como emisor o receptor."""
    ausentes = [d for d in resultado.documentos if not _menciona(d, cliente)]
    return ResultadoCuadre(
        codigo="C6",
        titulo="El cliente está en el listado",
        ok=not ausentes,
        detalle=(
            "no aparece en: " + _resumen([_referencia(d) for d in ausentes])
            if ausentes
            else f"{cliente.identificacion_formateada} aparece en todos los documentos"
        ),
    )


def cuadre_otros_impuestos(resultado: ResultadoMes) -> ResultadoCuadre:
    """C7: sin ICA, INC, timbre u otros impuestos distintos de IVA.

    Si alguno viene distinto de cero, `Total Neto = Total - IVA` deja de ser el valor
    antes de IVA y el neto quedaría silenciosamente incorrecto.
    """
    afectados = [d for d in resultado.documentos if d.impuestos_otros != 0]
    return ResultadoCuadre(
        codigo="C7",
        titulo="Solo IVA como impuesto",
        ok=not afectados,
        detalle=(
            "traen otros impuestos: "
            + _resumen([f"{_referencia(d)} ({d.impuestos_otros})" for d in afectados])
            if afectados
            else "todos los impuestos distintos de IVA están en cero"
        ),
    )


def ejecutar_cuadres(
    resultado: ResultadoMes,
    cliente: Cliente,
    periodo: Periodo,
    *,
    filas_dian: int,
    total_dian: Decimal,
) -> tuple[ResultadoCuadre, ...]:
    return (
        cuadre_cantidad(resultado, filas_dian),
        cuadre_total(resultado, total_dian),
        cuadre_cufe_unico(resultado),
        cuadre_bloques(resultado),
        cuadre_periodo(resultado, periodo),
        cuadre_cliente(resultado, cliente),
        cuadre_otros_impuestos(resultado),
    )


def hay_cuadres_fallidos(cuadres: tuple[ResultadoCuadre, ...]) -> bool:
    return any(not cuadre.ok and cuadre.bloqueante for cuadre in cuadres)
