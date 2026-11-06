"""Lector del listado de documentos electrónicos exportado por la DIAN.

Valida todo lo que puede venir mal (columnas, texto, fechas, números) y falla con un mensaje
que dice la fila y la columna exactas. Después de leer, el resto del código confía en los datos.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from openpyxl import load_workbook
from pydantic import ValidationError

from dian_hojas.dominio.enums import Categoria
from dian_hojas.dominio.modelos import DocumentoElectronico, ListadoDian
from dian_hojas.reglas.clasificador import clasificar, grupo_de

COLUMNAS_ESPERADAS: tuple[str, ...] = (
    "Tipo de documento",
    "CUFE/CUDE",
    "Folio",
    "Prefijo",
    "Divisa",
    "Forma de Pago",
    "Medio de Pago",
    "Fecha Emisión",
    "Fecha Recepción",
    "NIT Emisor",
    "Nombre Emisor",
    "NIT Receptor",
    "Nombre Receptor",
    "IVA",
    "ICA",
    "IC",
    "INC",
    "Timbre",
    "INC Bolsas",
    "IN Carbono",
    "IN Combustibles",
    "IC Datos",
    "ICL",
    "INPP",
    "IBUA",
    "ICUI",
    "Rete IVA",
    "Rete Renta",
    "Rete ICA",
    "Total",
    "Estado",
    "Grupo",
)

# Índices 1-based dentro de la fila.
COL_TIPO = 1
COL_CUFE = 2
COL_FOLIO = 3
COL_PREFIJO = 4
COL_DIVISA = 5
COL_FORMA_PAGO = 6
COL_MEDIO_PAGO = 7
COL_FECHA_EMISION = 8
COL_FECHA_RECEPCION = 9
COL_NIT_EMISOR = 10
COL_NOMBRE_EMISOR = 11
COL_NIT_RECEPTOR = 12
COL_NOMBRE_RECEPTOR = 13
COL_IVA = 14
COL_TOTAL = 30
COL_ESTADO = 31
COL_GRUPO = 32
COLUMNAS_OTROS_IMPUESTOS = (15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26)
COL_RETE_IVA = 27
COL_RETE_RENTA = 28
COL_RETE_ICA = 29

_FORMATOS_FECHA = ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d")


class ErrorListado(ValueError):
    """El archivo no tiene la forma esperada."""


def _error(fila: int, columna: str, detalle: str) -> ErrorListado:
    return ErrorListado(f"Fila {fila}, columna '{columna}': {detalle}")


def _texto_estricto(valor: object, fila: int, columna: str) -> str:
    """Texto que no admite pérdida de información (NIT, folio, CUFE)."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor.strip()
    if isinstance(valor, bool):
        raise _error(fila, columna, f"esperaba texto y llegó un booleano ({valor!r})")
    raise _error(
        fila,
        columna,
        f"esperaba texto y llegó un número ({valor!r}). "
        "Vuelve a exportar el archivo desde la DIAN: si Excel lo guardó como número, "
        "se perdieron ceros a la izquierda.",
    )


def _texto(valor: object, fila: int, columna: str) -> str:
    """Texto tolerante: convierte números a su representación entera."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor.strip()
    if isinstance(valor, bool):
        raise _error(fila, columna, f"esperaba texto y llegó un booleano ({valor!r})")
    if isinstance(valor, (int, float, Decimal)):
        numero = float(valor)
        return str(int(numero)) if numero.is_integer() else str(numero)
    raise _error(fila, columna, f"esperaba texto y llegó {type(valor).__name__}")


def _decimal(valor: object, fila: int, columna: str) -> Decimal:
    if valor is None or valor == "":
        return Decimal("0")
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, bool):
        raise _error(fila, columna, "esperaba un valor monetario y llegó un booleano")
    if isinstance(valor, (int, float)):
        return Decimal(str(valor))
    if isinstance(valor, str):
        try:
            return Decimal(valor.strip())
        except InvalidOperation as exc:
            raise _error(fila, columna, f"valor monetario inválido ({valor!r})") from exc
    raise _error(fila, columna, f"esperaba un valor monetario y llegó {type(valor).__name__}")


def _fecha(valor: object, fila: int, columna: str) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        texto = valor.strip()
        for formato in _FORMATOS_FECHA:
            try:
                return datetime.strptime(texto, formato).date()
            except ValueError:
                continue
    raise _error(fila, columna, f"fecha inválida ({valor!r}); se esperaba dd-mm-aaaa")


def _fecha_hora(valor: object, fila: int, columna: str) -> datetime:
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day)
    if isinstance(valor, str):
        texto = valor.strip()
        try:
            return datetime.fromisoformat(texto)
        except ValueError:
            for formato in ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"):
                try:
                    return datetime.strptime(texto, formato)
                except ValueError:
                    continue
    raise _error(fila, columna, f"fecha y hora inválida ({valor!r}); se esperaba formato ISO")


def _hoja(wb):
    if "Dian" in wb.sheetnames:
        return wb["Dian"]
    return wb.worksheets[0]


def _validar_encabezados(ws) -> None:
    encontrados = tuple(
        _texto(ws.cell(row=1, column=columna).value, 1, f"columna {columna}")
        for columna in range(1, len(COLUMNAS_ESPERADAS) + 1)
    )
    if encontrados == COLUMNAS_ESPERADAS:
        return
    for posicion, (esperado, encontrado) in enumerate(zip(COLUMNAS_ESPERADAS, encontrados), start=1):
        if esperado != encontrado:
            letra = chr(ord("A") + posicion - 1) if posicion <= 26 else f"columna {posicion}"
            raise ErrorListado(
                f"Encabezado inesperado en {letra}1: se esperaba '{esperado}' y llegó '{encontrado}'. "
                "El archivo no parece ser el listado de la DIAN."
            )
    raise ErrorListado(
        f"El listado debe tener {len(COLUMNAS_ESPERADAS)} columnas (A a AF) y llegaron {len(encontrados)}."
    )


def _documento(fila: int, valores: tuple[object, ...]) -> DocumentoElectronico:
    tipo_texto = _texto(valores[COL_TIPO - 1], fila, COLUMNAS_ESPERADAS[COL_TIPO - 1])
    grupo_texto = _texto(valores[COL_GRUPO - 1], fila, COLUMNAS_ESPERADAS[COL_GRUPO - 1])
    tipo, categoria = clasificar(tipo_texto, grupo_texto)

    otros = sum(
        (
            _decimal(valores[columna - 1], fila, COLUMNAS_ESPERADAS[columna - 1])
            for columna in COLUMNAS_OTROS_IMPUESTOS
        ),
        Decimal("0"),
    )

    try:
        return DocumentoElectronico(
            indice=fila - 2,
            tipo_texto=tipo_texto,
            grupo_texto=grupo_texto,
            tipo=tipo,
            grupo=grupo_de(grupo_texto),
            categoria=categoria,
            cufe=_texto_estricto(valores[COL_CUFE - 1], fila, "CUFE/CUDE"),
            folio=_texto_estricto(valores[COL_FOLIO - 1], fila, "Folio"),
            prefijo=_texto_estricto(valores[COL_PREFIJO - 1], fila, "Prefijo"),
            divisa=_texto(valores[COL_DIVISA - 1], fila, "Divisa"),
            forma_pago=_texto(valores[COL_FORMA_PAGO - 1], fila, "Forma de Pago"),
            medio_pago=_texto(valores[COL_MEDIO_PAGO - 1], fila, "Medio de Pago"),
            fecha_emision=_fecha(valores[COL_FECHA_EMISION - 1], fila, "Fecha Emisión"),
            fecha_recepcion=_fecha_hora(valores[COL_FECHA_RECEPCION - 1], fila, "Fecha Recepción"),
            nit_emisor=_texto_estricto(valores[COL_NIT_EMISOR - 1], fila, "NIT Emisor"),
            nombre_emisor=_texto(valores[COL_NOMBRE_EMISOR - 1], fila, "Nombre Emisor"),
            nit_receptor=_texto_estricto(valores[COL_NIT_RECEPTOR - 1], fila, "NIT Receptor"),
            nombre_receptor=_texto(valores[COL_NOMBRE_RECEPTOR - 1], fila, "Nombre Receptor"),
            iva=_decimal(valores[COL_IVA - 1], fila, "IVA"),
            impuestos_otros=otros,
            rete_iva=_decimal(valores[COL_RETE_IVA - 1], fila, COLUMNAS_ESPERADAS[COL_RETE_IVA - 1]),
            rete_renta=_decimal(valores[COL_RETE_RENTA - 1], fila, COLUMNAS_ESPERADAS[COL_RETE_RENTA - 1]),
            rete_ica=_decimal(valores[COL_RETE_ICA - 1], fila, COLUMNAS_ESPERADAS[COL_RETE_ICA - 1]),
            total=_decimal(valores[COL_TOTAL - 1], fila, "Total"),
            estado=_texto(valores[COL_ESTADO - 1], fila, "Estado"),
        )
    except ValidationError as exc:
        raise _error(fila, "documento", f"datos inválidos: {exc}") from exc


class LectorDianXlsx:
    """Adaptador de lectura para el Excel de la DIAN."""

    def leer(self, ruta: Path) -> ListadoDian:
        ruta = Path(ruta)
        if not ruta.is_file():
            raise ErrorListado(f"No existe el archivo {ruta}")

        wb = load_workbook(ruta, data_only=True)
        try:
            ws = _hoja(wb)
            _validar_encabezados(ws)

            documentos: list[DocumentoElectronico] = []
            total = Decimal("0")
            iva = Decimal("0")
            otros = Decimal("0")

            for fila, valores in enumerate(
                ws.iter_rows(min_row=2, max_col=len(COLUMNAS_ESPERADAS), values_only=True),
                start=2,
            ):
                if all(valor is None or valor == "" for valor in valores):
                    continue
                documento = _documento(fila, valores)
                documentos.append(documento)
                total += documento.total
                iva += documento.iva
                otros += documento.impuestos_otros
        finally:
            wb.close()

        return ListadoDian(
            documentos=tuple(documentos),
            filas=len(documentos),
            total=total,
            iva=iva,
            impuestos_otros=otros,
        )


def sin_clasificar(listado: ListadoDian) -> tuple[DocumentoElectronico, ...]:
    """Documentos que el clasificador no pudo ubicar. Se muestran, nunca se descartan."""
    return tuple(d for d in listado.documentos if d.categoria is Categoria.SIN_CLASIFICAR)
