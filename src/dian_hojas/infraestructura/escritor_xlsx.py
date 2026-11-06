"""Escritor del archivo Excel de la hoja de trabajo.

La pestaña `Dian` no se reconstruye: se **reutiliza el libro original** quitando las demás hojas.
Así queda intacta de verdad (valores, orden, estilos, anchos, panel inmovilizado y autofiltro),
sin riesgo de perder algo al copiar celda por celda (D-21).

Las hojas de trabajo sí se construyen desde cero, con fórmulas vivas y sin valores calculados en
Python (D-03, D-06).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from dian_hojas.dominio.modelos import Cliente, DocumentoElectronico, Periodo, ResultadoMes
from dian_hojas.infraestructura import estilos, plantilla
from dian_hojas.infraestructura.plantilla import DefinicionBloque, Hoja

HOJA_DIAN = "Dian"


class ErrorEscritura(RuntimeError):
    """No se puede generar el archivo con los datos que hay."""


def _numero(valor: Decimal) -> float:
    return float(valor)


def _texto_fecha(valor) -> str:
    return valor.strftime("%d-%m-%Y")


def _texto_fecha_hora(valor) -> str:
    return valor.strftime("%Y-%m-%dT%H:%M:%S")


class EscritorOpenpyxl:
    """Adaptador de escritura para las pestañas `Dian`, `Sumatorias`, `Ventas` y `Compras`."""

    def escribir(
        self,
        resultado: ResultadoMes,
        cliente: Cliente,
        periodo: Periodo,
        destino: Path,
        *,
        ruta_listado: Path,
    ) -> Path:
        destino = Path(destino)
        ruta_listado = Path(ruta_listado)

        if not resultado.en_hoja:
            raise ErrorEscritura(
                "El listado del mes no tiene documentos que llevar a las hojas; no se genera archivo."
            )
        if destino.resolve() == ruta_listado.resolve():
            raise ErrorEscritura(
                "El archivo de salida no puede ser el mismo listado de la DIAN: se perdería el original."
            )

        wb = load_workbook(ruta_listado)
        try:
            self._conservar_dian(wb)
            for hoja in (Hoja.SUMATORIAS, Hoja.VENTAS, Hoja.COMPRAS):
                ws = wb.create_sheet(str(hoja))
                self._construir_hoja(ws, hoja, resultado, cliente, periodo)
            wb.calculation.fullCalcOnLoad = True
            destino.parent.mkdir(parents=True, exist_ok=True)
            wb.save(destino)
        finally:
            wb.close()
        return destino

    # --- Hoja Dian ---------------------------------------------------------------------

    def _conservar_dian(self, wb) -> None:
        """Deja el libro con una sola hoja, la de la DIAN, y la llama `Dian`."""
        original = wb[HOJA_DIAN] if HOJA_DIAN in wb.sheetnames else wb.worksheets[0]
        for nombre in list(wb.sheetnames):
            if nombre != original.title:
                del wb[nombre]
        original.title = HOJA_DIAN

        # Los nombres definidos y los vínculos externos apuntaban a las hojas que se acaban de
        # borrar; si se quedan, Excel muestra #REF! al abrir.
        try:
            wb.defined_names.clear()
        except AttributeError:  # pragma: no cover - versiones antiguas de openpyxl
            pass
        enlaces = getattr(wb, "_external_links", None)
        if enlaces is not None:
            enlaces.clear()

    # --- Hojas de trabajo --------------------------------------------------------------

    def _construir_hoja(
        self,
        ws: Worksheet,
        hoja: Hoja,
        resultado: ResultadoMes,
        cliente: Cliente,
        periodo: Periodo,
    ) -> None:
        self._aplicar_anchos(ws)
        self._cabecera(ws, cliente, periodo)

        fila = 5
        if hoja is Hoja.SUMATORIAS:
            self._titulo(ws, fila, plantilla.TITULO_GENERAL, estilos.FUENTE_TITULO_BLOQUE)
            fila += 2
        else:
            ws.cell(row=fila, column=1, value=plantilla.ENCABEZADO_DIAN)
            ws.cell(row=fila, column=2, value=plantilla.ENCABEZADO_FISICA)

        fila_inicial = fila
        marcas = plantilla.hoja_lleva_marcas(hoja)
        for definicion in plantilla.bloques_de(hoja):
            documentos = resultado.documentos_de(definicion.bloque)
            if not documentos:
                continue
            if fila > fila_inicial:
                fila += 2
            fila = self._bloque(ws, fila, definicion, documentos, marcas=marcas)

        ws.freeze_panes = "A5"
        ws.auto_filter.ref = f"C4:T{ws.max_row}"

    def _aplicar_anchos(self, ws: Worksheet) -> None:
        for letra, ancho in estilos.ANCHOS.items():
            ws.column_dimensions[letra].width = ancho

    def _cabecera(self, ws: Worksheet, cliente: Cliente, periodo: Periodo) -> None:
        textos = (cliente.nombre, cliente.identificacion_formateada, periodo.titulo)
        for desplazamiento, texto in enumerate(textos):
            fila = 1 + desplazamiento
            for columna in range(
                plantilla.COLUMNA_TITULO_INICIAL, plantilla.COLUMNA_TITULO_FINAL + 1
            ):
                celda = ws.cell(row=fila, column=columna)
                celda.font = estilos.FUENTE_TITULO_GENERAL
                celda.fill = estilos.RELLENO_CLARO
                celda.alignment = estilos.ALINEACION_TITULO
            ws.cell(row=fila, column=plantilla.COLUMNA_TITULO_INICIAL, value=texto)
            ws.merge_cells(
                start_row=fila,
                start_column=plantilla.COLUMNA_TITULO_INICIAL,
                end_row=fila,
                end_column=plantilla.COLUMNA_TITULO_FINAL,
            )

        for columna in (1, 2):
            self._estilo_encabezado(ws.cell(row=4, column=columna))
        for desplazamiento, titulo in enumerate(plantilla.ENCABEZADOS):
            celda = ws.cell(
                row=4, column=plantilla.COLUMNA_INICIAL + desplazamiento, value=titulo
            )
            self._estilo_encabezado(celda)

    def _estilo_encabezado(self, celda) -> None:
        celda.font = estilos.FUENTE_ENCABEZADO
        celda.fill = estilos.RELLENO_ENCABEZADO
        celda.alignment = estilos.ALINEACION_ENCABEZADO

    def _titulo(self, ws: Worksheet, fila: int, texto: str, fuente) -> None:
        celda = ws.cell(row=fila, column=plantilla.COLUMNA_INICIAL, value=texto)
        celda.font = fuente
        celda.fill = estilos.RELLENO_TITULO
        celda.alignment = estilos.ALINEACION_BLOQUE

    def _bloque(
        self,
        ws: Worksheet,
        fila: int,
        definicion: DefinicionBloque,
        documentos: tuple[DocumentoElectronico, ...],
        *,
        marcas: bool,
    ) -> int:
        """Escribe título, filas de datos y total. Devuelve la fila siguiente a la del total."""
        self._titulo(ws, fila, definicion.titulo, estilos.FUENTE_TITULO_BLOQUE)
        fila += 1

        primera_datos = fila
        for documento in documentos:
            self._fila_documento(ws, fila, documento, marcas=marcas)
            fila += 1
        ultima_datos = fila - 1

        self._fila_total(ws, fila, definicion, primera_datos, ultima_datos)
        return fila + 1

    def _fila_documento(
        self,
        ws: Worksheet,
        fila: int,
        documento: DocumentoElectronico,
        *,
        marcas: bool,
    ) -> None:
        if marcas:
            for columna, valor in ((1, True), (2, False)):
                celda = ws.cell(row=fila, column=columna, value=valor)
                celda.font = estilos.FUENTE_DATO
                celda.alignment = estilos.ALINEACION_BOOLEANO

        valores = (
            documento.tipo_texto,
            documento.cufe,
            documento.folio,
            documento.prefijo,
            documento.divisa,
            documento.forma_pago,
            documento.medio_pago,
            _texto_fecha(documento.fecha_emision),
            _texto_fecha_hora(documento.fecha_recepcion),
            documento.nit_emisor,
            documento.nombre_emisor,
            documento.nit_receptor,
            documento.nombre_receptor,
            _numero(documento.iva),
            f"=R{fila}-P{fila}",
            _numero(documento.total),
            documento.estado,
            documento.grupo_texto,
        )
        columnas_dinero = (
            plantilla.COLUMNA_IVA,
            plantilla.COLUMNA_TOTAL_NETO,
            plantilla.COLUMNA_TOTAL,
        )
        for desplazamiento, valor in enumerate(valores):
            columna = plantilla.COLUMNA_INICIAL + desplazamiento
            celda = ws.cell(row=fila, column=columna, value=valor)
            if columna in columnas_dinero:
                celda.font = estilos.FUENTE_DATO_MONETARIO
                celda.number_format = estilos.FORMATO_MONEDA
                celda.fill = estilos.RELLENO_CLARO
            else:
                celda.font = estilos.FUENTE_DATO
            celda.alignment = estilos.ALINEACION_DATO

    def _fila_total(
        self,
        ws: Worksheet,
        fila: int,
        definicion: DefinicionBloque,
        primera_datos: int,
        ultima_datos: int,
    ) -> None:
        etiqueta = ws.cell(
            row=fila, column=plantilla.COLUMNA_ETIQUETA_TOTAL, value=definicion.etiqueta_total
        )
        etiqueta.font = estilos.FUENTE_TOTAL_ETIQUETA
        etiqueta.alignment = estilos.ALINEACION_DATO

        for columna in (
            plantilla.COLUMNA_IVA,
            plantilla.COLUMNA_TOTAL_NETO,
            plantilla.COLUMNA_TOTAL,
        ):
            letra = get_column_letter(columna)
            celda = ws.cell(
                row=fila,
                column=columna,
                value=f"=SUM({letra}{primera_datos}:{letra}{ultima_datos})",
            )
            celda.font = estilos.FUENTE_TOTAL_VALOR
            celda.number_format = estilos.FORMATO_MONEDA
            celda.fill = estilos.RELLENO_CLARO
