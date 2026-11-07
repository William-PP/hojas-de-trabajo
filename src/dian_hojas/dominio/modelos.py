"""Modelos del dominio. Python puro: sin pandas, openpyxl, PySide6 ni sqlite3."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dian_hojas.dominio.enums import (
    Bloque,
    Categoria,
    Grupo,
    TipoDocumento,
    bloque_de,
)

MESES = (
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
)

MESES_ABREV = (
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
)

_CARACTERES_INVALIDOS = re.compile(r'[<>:"/\\|?*]')
_SOLO_DIGITOS = re.compile(r"\D")

CERO = Decimal("0")


class Cliente(BaseModel):
    """Cliente para el que se prepara la hoja."""

    model_config = ConfigDict(frozen=True)

    nombre: str = Field(min_length=1)
    tipo_identificacion: Literal["NIT", "CC"] = "NIT"
    numero: str = Field(min_length=1)
    digito_verificacion: str | None = None

    @field_validator("nombre", "numero")
    @classmethod
    def _sin_espacios_exteriores(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("no puede estar vacío")
        return limpio

    @property
    def numero_digitos(self) -> str:
        """Solo los dígitos del número, sin puntos, guiones ni dígito de verificación."""
        return _SOLO_DIGITOS.sub("", self.numero)

    @property
    def identificacion_formateada(self) -> str:
        """`NIT. 901.320.747-4` o `CC. 1.020.396.459`."""
        digitos = self.numero_digitos
        with_dots = f"{int(digitos):,}".replace(",", ".") if digitos.isdigit() else digitos
        texto = f"{self.tipo_identificacion}. {with_dots}"
        if self.tipo_identificacion == "NIT" and self.digito_verificacion:
            texto = f"{texto}-{self.digito_verificacion.strip()}"
        return texto


class PerfilCliente(BaseModel):
    """Datos del cliente que se recuerdan entre meses (Fase 4).

    La identificación se guarda como texto (regla 8) y la carpeta de salida es opcional: si viene
    vacía, la interfaz conserva la que el usuario tenga en ese momento.
    """

    model_config = ConfigDict(frozen=True)

    cliente: Cliente
    carpeta_salida: str = ""


class Periodo(BaseModel):
    """Mes y año que se están trabajando."""

    model_config = ConfigDict(frozen=True)

    anio: int = Field(ge=2000, le=2100)
    mes: int = Field(ge=1, le=12)

    @property
    def nombre_mes(self) -> str:
        return MESES[self.mes - 1]

    @property
    def mes_abrev(self) -> str:
        return MESES_ABREV[self.mes - 1]

    @property
    def primer_dia(self) -> date:
        return date(self.anio, self.mes, 1)

    @property
    def ultimo_dia(self) -> date:
        return date(self.anio, self.mes, calendar.monthrange(self.anio, self.mes)[1])

    @property
    def titulo(self) -> str:
        return f"LISTADO DOCUMENTOS ELECTRONICOS DIAN {self.nombre_mes} {self.anio}"

    def contiene(self, fecha: date) -> bool:
        return fecha.year == self.anio and fecha.month == self.mes

    def nombre_archivo(self, cliente: Cliente) -> str:
        nombre = _CARACTERES_INVALIDOS.sub("", cliente.nombre).strip()
        nombre = "_".join(nombre.split())
        return f"{self.mes:02d}-Hoja_de_trabajo_Rtefte_{self.mes_abrev}_{self.anio}_{nombre}.xlsx"


class DocumentoElectronico(BaseModel):
    """Una fila del listado de la DIAN, ya clasificada."""

    model_config = ConfigDict(frozen=True)

    indice: int = Field(ge=0)
    tipo_texto: str
    grupo_texto: str
    tipo: TipoDocumento | None = None
    grupo: Grupo | None = None
    categoria: Categoria = Categoria.SIN_CLASIFICAR

    cufe: str = Field(min_length=1)
    folio: str = Field(min_length=1)
    prefijo: str = ""
    divisa: str = ""
    forma_pago: str = ""
    medio_pago: str = ""

    fecha_emision: date
    fecha_recepcion: datetime

    nit_emisor: str = ""
    nombre_emisor: str = ""
    nit_receptor: str = ""
    nombre_receptor: str = ""

    iva: Decimal = CERO
    impuestos_otros: Decimal = CERO
    rete_iva: Decimal = CERO
    rete_renta: Decimal = CERO
    rete_ica: Decimal = CERO
    total: Decimal = CERO

    estado: str = ""

    @property
    def total_neto(self) -> Decimal:
        return self.total - self.iva

    @property
    def bloque(self) -> Bloque | None:
        return bloque_de(self.categoria)


@dataclass(frozen=True, slots=True)
class ListadoDian:
    """Resultado de leer el archivo de la DIAN."""

    documentos: tuple[DocumentoElectronico, ...]
    filas: int
    total: Decimal
    iva: Decimal
    impuestos_otros: Decimal

    @property
    def vacio(self) -> bool:
        return self.filas == 0


@dataclass(frozen=True, slots=True)
class ResultadoMes:
    """Documentos agrupados en los bloques de la hoja."""

    documentos: tuple[DocumentoElectronico, ...]
    bloques: dict[Bloque, tuple[DocumentoElectronico, ...]]
    excluidos: tuple[DocumentoElectronico, ...]
    no_clasificados: tuple[DocumentoElectronico, ...]

    def documentos_de(self, bloque: Bloque) -> tuple[DocumentoElectronico, ...]:
        return self.bloques.get(bloque, ())

    @property
    def en_hoja(self) -> tuple[DocumentoElectronico, ...]:
        return tuple(d for bloque in self.bloques.values() for d in bloque)

    @property
    def total(self) -> Decimal:
        return sum((d.total for d in self.en_hoja), CERO)

    @property
    def iva(self) -> Decimal:
        return sum((d.iva for d in self.en_hoja), CERO)

    @property
    def total_neto(self) -> Decimal:
        return sum((d.total_neto for d in self.en_hoja), CERO)


def agrupar_en_bloques(
    documentos: tuple[DocumentoElectronico, ...],
) -> dict[Bloque, tuple[DocumentoElectronico, ...]]:
    """Agrupa por bloque, ordenando por fecha de emisión descendente.

    El orden es estable: ante fechas iguales se respeta el orden del listado.
    """
    grupos: dict[Bloque, list[DocumentoElectronico]] = {bloque: [] for bloque in Bloque}
    for documento in documentos:
        if documento.bloque is not None:
            grupos[documento.bloque].append(documento)

    ordenados: dict[Bloque, tuple[DocumentoElectronico, ...]] = {}
    for bloque, filas in grupos.items():
        por_indice = sorted(filas, key=lambda d: d.indice)
        ordenados[bloque] = tuple(sorted(por_indice, key=lambda d: d.fecha_emision, reverse=True))
    return ordenados


def construir_resultado(documentos: tuple[DocumentoElectronico, ...]) -> ResultadoMes:
    return ResultadoMes(
        documentos=documentos,
        bloques=agrupar_en_bloques(documentos),
        excluidos=tuple(d for d in documentos if d.categoria is Categoria.RESPUESTA_DIAN),
        no_clasificados=tuple(d for d in documentos if d.categoria is Categoria.SIN_CLASIFICAR),
    )
