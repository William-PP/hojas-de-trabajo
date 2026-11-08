"""Fábrica de documentos para las pruebas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from dian_hojas.dominio.modelos import DocumentoElectronico
from dian_hojas.reglas.clasificador import clasificar, grupo_de


def documento(**cambios: Any) -> DocumentoElectronico:
    """Un documento válido con todos los campos; cambia solo los que interesan."""
    datos: dict[str, Any] = {
        "indice": 0,
        "tipo_texto": "Factura electrónica",
        "grupo_texto": "Recibido",
        "cufe": "cufe-de-relleno-0001",
        "folio": "1001",
        "prefijo": "FV",
        "divisa": "COP",
        "forma_pago": "1",
        "medio_pago": "31",
        "fecha_emision": date(2026, 10, 15),
        "fecha_recepcion": datetime(2026, 10, 15, 9, 30, 0),
        "nit_emisor": "900123456",
        "nombre_emisor": "PROVEEDOR UNO",
        "nit_receptor": "900000001",
        "nombre_receptor": "CLIENTE UNO",
        "iva": Decimal("1900.00"),
        "total": Decimal("11900.00"),
        "estado": "Aprobado",
    }
    datos.update(cambios)

    tipo, categoria = clasificar(datos["tipo_texto"], datos["grupo_texto"])
    datos.setdefault("tipo", tipo)
    datos.setdefault("grupo", grupo_de(datos["grupo_texto"]))
    datos.setdefault("categoria", categoria)
    return DocumentoElectronico(**datos)
