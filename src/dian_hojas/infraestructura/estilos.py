"""Estilos visuales de las hojas de trabajo.

Todo lo cosmético vive aquí y en ningún otro sitio. Los valores se midieron en la hoja de
referencia (D-16); el golden no los compara, pero así la salida se ve igual a la que ya se usa.
"""

from __future__ import annotations

from openpyxl.styles import Alignment, Font, PatternFill

FUENTE = "Calibri"

RELLENO_ENCABEZADO = PatternFill(fill_type="solid", fgColor="FF348441")
RELLENO_TITULO = PatternFill(fill_type="solid", fgColor="FFDBE5F1")
RELLENO_CLARO = PatternFill(fill_type="solid", fgColor="FFFFFFFF")

FUENTE_ENCABEZADO = Font(name=FUENTE, size=10, bold=True, color="FFFFFFFF")
FUENTE_TITULO_GENERAL = Font(name=FUENTE, size=12, bold=True)
FUENTE_TITULO_BLOQUE = Font(name=FUENTE, size=11, bold=True)
FUENTE_DATO = Font(name=FUENTE, size=10, color="FF000000")
# En la referencia las columnas de dinero van un punto más grandes que el resto de la fila.
FUENTE_DATO_MONETARIO = Font(name=FUENTE, size=11)
FUENTE_TOTAL_ETIQUETA = Font(name=FUENTE, size=10, bold=True, color="FF000000")
FUENTE_TOTAL_VALOR = Font(name=FUENTE, size=11, bold=True)

ALINEACION_ENCABEZADO = Alignment(horizontal="center", vertical="center")
ALINEACION_TITULO = Alignment(horizontal="center", vertical="bottom")
ALINEACION_BLOQUE = Alignment(vertical="bottom")
ALINEACION_DATO = Alignment(vertical="bottom", wrap_text=False)
ALINEACION_BOOLEANO = Alignment(horizontal="center", vertical="bottom")

# Moneda sin decimales, con negativos en rojo y entre paréntesis de dólar, como en la referencia.
FORMATO_MONEDA = '"$"\\ #,##0;[Red]\\-"$"\\ #,##0'

# D-16. Anchos uniformes para las tres hojas; la referencia los tenía inconsistentes entre pestañas.
ANCHOS: dict[str, float] = {
    "A": 5.43,
    "B": 8.43,
    "C": 8.7,
    "D": 13.0,
    "E": 13.0,
    "F": 13.0,
    "G": 13.0,
    "H": 13.0,
    "I": 13.0,
    "J": 13.0,
    "K": 13.0,
    "L": 13.0,
    "M": 35.6,
    "N": 8.7,
    "O": 35.6,
    "P": 12.1,
    "Q": 13.9,
    "R": 12.7,
    "S": 8.7,
    "T": 13.0,
    "U": 20.0,
    "V": 14.0,
    "W": 14.0,
    "X": 12.0,
    "Y": 12.0,
    "Z": 12.0,
    "AA": 30.0,
}
