"""Generador del listado DIAN sintético usado por las pruebas.

Datos inventados: no contiene información de ningún cliente real.
Se construye en memoria y se guarda en la ruta que pida la prueba, para no versionar binarios.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from dian_hojas.dominio.enums import Categoria
from dian_hojas.infraestructura.lector_dian_xlsx import COLUMNAS_ESPERADAS
from dian_hojas.reglas.clasificador import clasificar

CLIENTE_NIT = "900000001"
PROVEEDOR_NIT = "900123456"
OTRO_NIT = "800999111"


def _cufe(numero: int) -> str:
    return f"{numero:02d}".ljust(96, "a")


def _fila(
    numero: int,
    *,
    tipo: str = "Factura electrónica",
    grupo: str = "Recibido",
    folio: str = "1001",
    prefijo: str = "FV",
    fecha: str = "15-10-2026",
    recepcion: str = "2026-10-15T09:30:00",
    emisor: str = PROVEEDOR_NIT,
    nombre_emisor: str = "PROVEEDOR SINTETICO UNO",
    receptor: str = CLIENTE_NIT,
    nombre_receptor: str = "CLIENTE SINTETICO SAS",
    iva: str = "1900.00",
    total: str = "11900.00",
    inc: str = "0",
    estado: str = "Aprobado",
    divisa: str = "COP",
    forma_pago: str = "1",
    medio_pago: str = "31",
) -> dict[str, object]:
    """Una fila completa del listado, con valores por defecto válidos."""
    return {
        "Tipo de documento": tipo,
        "CUFE/CUDE": _cufe(numero),
        "Folio": folio,
        "Prefijo": prefijo,
        "Divisa": divisa,
        "Forma de Pago": forma_pago,
        "Medio de Pago": medio_pago,
        "Fecha Emisión": fecha,
        "Fecha Recepción": recepcion,
        "NIT Emisor": emisor,
        "Nombre Emisor": nombre_emisor,
        "NIT Receptor": receptor,
        "Nombre Receptor": nombre_receptor,
        "IVA": Decimal(iva),
        "INC": Decimal(inc),
        "Total": Decimal(total),
        "Estado": estado,
        "Grupo": grupo,
    }


FILAS_BASE: tuple[dict[str, object], ...] = (
    # 1 y 2: ventas (el cliente es el emisor)
    _fila(
        1,
        grupo="Emitido",
        folio="197",
        fecha="20-10-2026",
        recepcion="2026-10-20T10:42:17",
        emisor=CLIENTE_NIT,
        nombre_emisor="CLIENTE SINTETICO SAS",
        receptor=OTRO_NIT,
        nombre_receptor="COMPRADOR SINTETICO",
        iva="87400.00",
        total="547400.00",
        estado="Aprobado con notificación",
    ),
    _fila(
        2,
        grupo="Emitido",
        folio="000123",
        prefijo="",
        fecha="05-10-2026",
        recepcion="2026-10-05T08:00:00",
        emisor=CLIENTE_NIT,
        nombre_emisor="CLIENTE SINTETICO SAS",
        receptor=OTRO_NIT,
        nombre_receptor="COMPRADOR SINTETICO",
        iva="0",
        total="50000.00",
    ),
    # 3 a 5: compras
    _fila(
        3,
        folio="2002",
        prefijo="CFL",
        fecha="31-10-2026",
        recepcion="2026-10-31T12:07:18",
        iva="26297.00",
        total="164704.00",
    ),
    _fila(
        4,
        folio="1457",
        prefijo="CFL",
        fecha="15-10-2026",
        recepcion="2026-10-15T16:00:00",
        iva="1900.00",
        total="11900.00",
    ),
    _fila(
        5,
        folio="16",
        prefijo="CFL",
        fecha="01-10-2026",
        recepcion="2026-10-01T09:00:00",
        iva="100.00",
        total="1100.00",
    ),
    # 6: documento soporte emitido (aun así es compra)
    _fila(
        6,
        tipo="Documento soporte con no obligados",
        grupo="Emitido",
        folio="35",
        prefijo="DSRH",
        fecha="18-10-2026",
        recepcion="2026-10-18T13:10:05",
        emisor=CLIENTE_NIT,
        nombre_emisor="CLIENTE SINTETICO SAS",
        receptor=OTRO_NIT,
        nombre_receptor="NO OBLIGADO SINTETICO",
        iva="0",
        total="250000.00",
    ),
    # 7: documento soporte recibido (compra)
    _fila(
        7,
        tipo="Documento soporte con no obligados",
        folio="36",
        prefijo="DSPO",
        fecha="12-10-2026",
        recepcion="2026-10-12T11:00:00",
        iva="0",
        total="180000.00",
    ),
    # 8: documento equivalente (servicios públicos)
    _fila(
        8,
        tipo="Documento equivalente - Servicios públicos domiciliarios",
        folio="778899",
        prefijo="EPM",
        fecha="09-10-2026",
        recepcion="2026-10-09T07:45:00",
        iva="0",
        total="95000.00",
    ),
    # 9 y 10: notas crédito recibidas, con folio alfanumérico
    _fila(
        9,
        tipo="Nota de crédito electrónica",
        folio="NCP14858",
        prefijo="",
        fecha="30-10-2026",
        recepcion="2026-10-30T18:00:00",
        iva="125639.78",
        total="786901.78",
    ),
    _fila(
        10,
        tipo="Nota de crédito electrónica",
        folio="C0039827",
        prefijo="NCP",
        fecha="02-10-2026",
        recepcion="2026-10-02T10:00:00",
        iva="9400.00",
        total="58899.98",
    ),
    # 11: nota crédito emitida (devolución en ventas)
    _fila(
        11,
        tipo="Nota de crédito electrónica",
        grupo="Emitido",
        folio="NC-01",
        prefijo="NC",
        fecha="28-10-2026",
        recepcion="2026-10-28T15:00:00",
        emisor=CLIENTE_NIT,
        nombre_emisor="CLIENTE SINTETICO SAS",
        receptor=OTRO_NIT,
        nombre_receptor="COMPRADOR SINTETICO",
        iva="12000.00",
        total="78000.00",
    ),
    # 12: nómina (emitida, pero es un costo)
    _fila(
        12,
        tipo="Nomina Individual",
        grupo="Emitido",
        folio="9",
        prefijo="NOM",
        divisa="",
        forma_pago="",
        medio_pago="",
        fecha="01-10-2026",
        recepcion="2026-10-01T15:58:54",
        emisor=CLIENTE_NIT,
        nombre_emisor="CLIENTE SINTETICO SAS",
        receptor="",
        nombre_receptor="EMPLEADO SINTETICO",
        iva="0",
        total="2259927.60",
    ),
    # 13: respuesta de la DIAN, no es documento contable
    _fila(
        13,
        tipo="Application response",
        folio="AR-1",
        prefijo="AR",
        fecha="31-10-2026",
        recepcion="2026-10-31T13:00:00",
        iva="0",
        total="0",
    ),
)


def crear_listado(
    ruta: Path,
    *,
    duplicado: bool = False,
    fuera_de_periodo: bool = False,
    desconocido: bool = False,
    otros_impuestos: bool = False,
) -> Path:
    """Escribe el listado sintético y devuelve la ruta."""
    filas = list(FILAS_BASE)

    if duplicado:
        filas.append(_fila(20, folio="9999", prefijo="DUP", total="1000.00", iva="0"))
        filas[-1]["CUFE/CUDE"] = _cufe(3)
    if fuera_de_periodo:
        filas.append(
            _fila(21, folio="SEP-1", fecha="30-09-2026", recepcion="2026-09-30T10:00:00")
        )
    if desconocido:
        filas.append(_fila(22, tipo="Documento raro de otro país", folio="RARO-1"))
    if otros_impuestos:
        filas.append(_fila(23, folio="INC-1", inc="5000.00", total="16900.00"))

    wb = Workbook()
    ws = wb.active
    ws.title = "Dian"
    ws.append(list(COLUMNAS_ESPERADAS))
    for fila in filas:
        ws.append([fila.get(columna) for columna in COLUMNAS_ESPERADAS])
    # Igual que una exportación real de la DIAN: panel fijo y autofiltro sobre los datos.
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:AF{len(filas) + 1}"
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta)
    wb.close()
    return ruta


def categoria(fila: int) -> Categoria:
    """Categoría esperada para una fila de `FILAS_BASE` (0-based)."""
    datos = FILAS_BASE[fila]
    return clasificar(str(datos["Tipo de documento"]), str(datos["Grupo"]))[1]


def total_de(fila: int) -> Decimal:
    return Decimal(str(FILAS_BASE[fila]["Total"]))
