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
from typing import Collection

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from dian_hojas.dominio.modelos import Cliente, DocumentoElectronico, Periodo, ResultadoMes
from dian_hojas.dominio.retefuente import RetefuenteMes
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
        retefuente: RetefuenteMes | None = None,
        soportes_verificados: Collection[str] | None = None,
        otros_confirmados: bool = False,
    ) -> Path:
        destino = Path(destino)
        ruta_listado = Path(ruta_listado)
        verificados = frozenset(soportes_verificados or ())

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
                self._construir_hoja(ws, hoja, resultado, cliente, periodo, verificados, otros_confirmados)
            if retefuente is not None and retefuente.lineas:
                ws = wb.create_sheet(plantilla.nombre_hoja_retefuente(periodo))
                self._construir_retefuente(ws, periodo, retefuente, cliente, verificados)
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
        # La DIAN trae un FilterDatabase propio en la hoja; si se deja, openpyxl agrega otro
        # al guardar y Excel rechaza el archivo como corrupto (duplicado por hoja).
        try:
            original.defined_names.clear()
        except AttributeError:
            pass
        # Vistas de filtro personalizadas de la hoja original también dejan nombres huérfanos.
        try:
            original._views = []
        except AttributeError:
            pass
        # La tabla de Excel de la DIAN (style "Dian-style" de Google Sheets) deja un
        # `tableParts` que Excel rechaza al guardar como .xlsx. Se quita de la copia;
        # los datos, el autofiltro y el panel fijo quedan intactos (D-54).
        try:
            original._tables = {}
        except AttributeError:
            pass
        try:
            if hasattr(original, "tables"):
                original.tables.clear()
        except AttributeError:
            pass
        # El listado DIAN trae filas vacías con formato hasta la fila 1000. openpyxl las
        # guarda como `<c t="n"/>` sin valor y Excel las rechaza como contenido corrupto.
        # Recorta esas filas vacías de la copia (el original no se toca); los datos 1..N
        # quedan intactos. También hay que borrar sus altos/estilos (`row_dimensions`),
        # si no Excel ve dimensión AF90 con filas hasta 1000 y de nuevo lo rechaza.
        ultima_con_datos = 1
        for fila in range(original.max_row, 0, -1):
            for columna in range(1, 33):
                if original.cell(row=fila, column=columna).value not in (None, ""):
                    ultima_con_datos = fila
                    break
            else:
                continue
            break
        if ultima_con_datos < original.max_row:
            original.delete_rows(ultima_con_datos + 1, original.max_row - ultima_con_datos)
            for numero_fila in list(original.row_dimensions.keys()):
                if numero_fila > ultima_con_datos:
                    del original.row_dimensions[numero_fila]
            # Las celdas con formato pero sin valor también dejan `<c t="n"/>` inválido.
            for fila in range(1, ultima_con_datos + 1):
                for columna in range(1, 33):
                    celda = original.cell(row=fila, column=columna)
                    if celda.value in (None, ""):
                        # Elimina la celda vacía con formato: así no se genera `t="n"`.
                        original._cells.pop((fila, columna), None)
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
        verificados: frozenset[str],
        otros_confirmados: bool = False,
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
        filas_totales: dict = {}
        for definicion in plantilla.bloques_de(hoja):
            documentos = resultado.documentos_de(definicion.bloque)
            if not documentos:
                continue
            if fila > fila_inicial:
                fila += 2
            antes = fila
            fila = self._bloque(ws, fila, definicion, documentos, marcas=marcas, verificados=verificados)
            filas_totales[definicion.bloque] = antes + 1 + len(documentos)

        fila = self._lineas_netas(ws, hoja, filas_totales, fila)

        if hoja is Hoja.SUMATORIAS and otros_confirmados:
            celda_nota = ws.cell(row=1, column=3, value=plantilla.NOTA_OTROS_CONFIRMADOS)
            celda_nota.font = estilos.FUENTE_DATO
            celda_nota.alignment = estilos.ALINEACION_BLOQUE

        ws.freeze_panes = "A5"
        if hoja is Hoja.SUMATORIAS:
            # D-51: varios bloques; sin autofiltro.
            ws.auto_filter.ref = None
        else:
            ultima_datos = max(filas_totales.values()) - 1 if filas_totales else 4
            ws.auto_filter.ref = f"C4:U{ultima_datos}"

    def _construir_retefuente(
        self,
        ws: Worksheet,
        periodo,
        retefuente,
        cliente: Cliente,
        verificados: frozenset[str],
    ) -> None:
        """Pestaña `Retefuente [Mes]`: copia de las compras con columnas de trabajo a la derecha."""
        self._aplicar_anchos(ws)
        self._cabecera(ws, cliente, periodo)
        for titulo, columna in plantilla.COLUMNAS_RETIFUERTE:
            self._estilo_encabezado(ws.cell(row=4, column=columna, value=titulo))

        fila = 5
        for linea in retefuente.lineas:
            self._escribir_documento(ws, fila, linea.documento, marcas=True, verificados=verificados)
            self._escribir_campo_retefuente(ws, fila, linea)
            fila += 1
        ultima_datos = fila - 1
        self._resumen_retefuente(ws, fila, retefuente)

        ws.freeze_panes = "A5"
        ws.auto_filter.ref = f"C4:AB{ultima_datos}"

    def _escribir_campo_retefuente(self, ws: Worksheet, fila: int, linea) -> None:
        pendiente = not linea.confirmada
        concepto_visible = f"{linea.concepto} — PENDIENTE DE CONFIRMAR" if pendiente else linea.concepto
        campos = (
            (plantilla.COLUMNA_RETIFUERTE_CONCEPTO, concepto_visible, estilos.FUENTE_DATO, None),
            (plantilla.COLUMNA_RETIFUERTE_BASE, _numero(linea.base), estilos.FUENTE_DATO_MONETARIO, estilos.FORMATO_MONEDA),
            (plantilla.COLUMNA_RETIFUERTE_BASE_MIN, linea.base_minima_uvt, estilos.FUENTE_DATO, None),
            (plantilla.COLUMNA_RETIFUERTE_SUPERA, "Sí" if linea.supera_base else "No", estilos.FUENTE_DATO, None),
            (plantilla.COLUMNA_RETIFUERTE_TARIFA, linea.tarifa, estilos.FUENTE_DATO_MONETARIO, estilos.FORMATO_MONEDA),
            (plantilla.COLUMNA_RETIFUERTE_RETENCION, linea.retencion, estilos.FUENTE_DATO_MONETARIO, estilos.FORMATO_MONEDA),
            (plantilla.COLUMNA_RETIFUERTE_OBS, f"Proveedor {linea.documento.nit_emisor}" if linea.documento else "", estilos.FUENTE_DATO, None),
        )
        for columna, valor, fuente, formato in campos:
            celda = ws.cell(row=fila, column=columna, value=valor)
            celda.font = fuente
            if pendiente:
                celda.fill = estilos.RELLENO_PENDIENTE
            if formato is not None:
                celda.number_format = formato

    def _parametros_retefuente(self, ws: Worksheet, fila: int, retefuente) -> int:
        """Escribe año, UVT y tarifa/base de cada concepto usado (D-49)."""
        if retefuente.anio is None and not retefuente.conceptos:
            return fila
        etiqueta = ws.cell(
            row=fila,
            column=plantilla.COLUMNA_RETIFUERTE_CONCEPTO,
            value=f"Año {retefuente.anio} · UVT {retefuente.uvt_pesos}",
        )
        etiqueta.font = estilos.FUENTE_TOTAL_ETIQUETA
        siguiente = fila + 1
        for nombre, base_minima, tarifa in retefuente.conceptos:
            ws.cell(row=siguiente, column=plantilla.COLUMNA_RETIFUERTE_CONCEPTO, value=nombre).font = estilos.FUENTE_DATO
            ws.cell(row=siguiente, column=plantilla.COLUMNA_RETIFUERTE_BASE_MIN, value=base_minima).font = estilos.FUENTE_DATO
            ws.cell(row=siguiente, column=plantilla.COLUMNA_RETIFUERTE_TARIFA, value=tarifa).font = estilos.FUENTE_DATO_MONETARIO
            ws.cell(row=siguiente, column=plantilla.COLUMNA_RETIFUERTE_TARIFA).number_format = estilos.FORMATO_MONEDA
            siguiente += 1
        return siguiente

    def _resumen_retefuente(self, ws: Worksheet, fila: int, retefuente) -> int:
        """Resumen final por concepto y total (PROVISIONAL si hay pendientes)."""
        grupos: dict[str, list] = {}
        for linea in retefuente.lineas:
            grupos.setdefault(linea.concepto, []).append(linea)

        siguiente = fila
        for concepto in sorted(grupos):
            grupo = grupos[concepto]
            base_total = sum((linea.base for linea in grupo), Decimal("0"))
            retencion_total = sum((linea.retencion for linea in grupo), Decimal("0"))
            self._escribir_resumen_retefuente(ws, siguiente, concepto, base_total, retencion_total)
            siguiente += 1

        if retefuente.hay_pendientes:
            etiqueta_total = (
                f"TOTAL RETENCIÓN PROVISIONAL ({retefuente.cantidad_pendientes} pendiente(s))"
            )
        else:
            etiqueta_total = "TOTAL RETENCIÓN A DECLARAR"
        self._escribir_resumen_retefuente(
            ws, siguiente, etiqueta_total, retefuente.total_retencion, retefuente.total_retencion
        )
        siguiente += 1
        siguiente = self._parametros_retefuente(ws, siguiente, retefuente)
        return siguiente

    def _escribir_resumen_retefuente(
        self,
        ws: Worksheet,
        fila: int,
        concepto: str,
        base_total: Decimal,
        retencion_total: Decimal,
    ) -> None:
        etiqueta = ws.cell(row=fila, column=plantilla.COLUMNA_RETIFUERTE_CONCEPTO, value=concepto)
        etiqueta.font = estilos.FUENTE_TOTAL_ETIQUETA
        base = ws.cell(row=fila, column=plantilla.COLUMNA_RETIFUERTE_BASE, value=_numero(base_total))
        base.font = estilos.FUENTE_DATO
        retencion = ws.cell(row=fila, column=plantilla.COLUMNA_RETIFUERTE_RETENCION, value=_numero(retencion_total))
        retencion.font = estilos.FUENTE_TOTAL_VALOR
        retencion.number_format = estilos.FORMATO_MONEDA

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

        for desplazamiento, titulo in enumerate(plantilla.ENCABEZADOS):
            celda = ws.cell(
                row=4, column=plantilla.COLUMNA_INICIAL + desplazamiento, value=titulo
            )
            self._estilo_encabezado(celda)
        celda_otros = ws.cell(row=4, column=plantilla.COLUMNA_OTROS, value="Otros impuestos")
        self._estilo_encabezado(celda_otros)

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
        verificados: frozenset[str],
    ) -> int:
        """Escribe título, filas de datos y total. Devuelve la fila siguiente a la del total."""
        self._titulo(ws, fila, definicion.titulo, estilos.FUENTE_TITULO_BLOQUE)
        fila += 1

        primera_datos = fila
        for documento in documentos:
            self._fila_documento(ws, fila, documento, marcas=marcas, verificados=verificados)
            fila += 1
        ultima_datos = fila - 1

        self._fila_total(ws, fila, definicion, primera_datos, ultima_datos)
        return fila + 1

    def _lineas_netas(self, ws: Worksheet, hoja, filas_totales: dict, fila: int) -> int:
        """COMPRAS NETAS (y VENTAS NETAS si hay devoluciones en ventas), pura fórmula viva.

        No toca los bloques ni sus signos (D-12) y no es un bloque: no entra en C1–C7.
        """
        from dian_hojas.dominio.enums import Bloque

        fila += 1
        if hoja in (Hoja.SUMATORIAS, Hoja.COMPRAS) and Bloque.FACTURAS_COMPRAS in filas_totales and Bloque.DEVOLUCIONES_COMPRAS in filas_totales:
            fila = self._fila_neta(
                ws, fila, plantilla.ETIQUETA_COMPRAS_NETAS,
                filas_totales[Bloque.FACTURAS_COMPRAS], filas_totales[Bloque.DEVOLUCIONES_COMPRAS],
            )
            fila += 1
        if hoja in (Hoja.SUMATORIAS, Hoja.VENTAS) and Bloque.FACTURAS_VENTAS in filas_totales and Bloque.DEVOLUCIONES_VENTAS in filas_totales:
            fila = self._fila_neta(
                ws, fila, plantilla.ETIQUETA_VENTAS_NETAS,
                filas_totales[Bloque.FACTURAS_VENTAS], filas_totales[Bloque.DEVOLUCIONES_VENTAS],
            )
            fila += 1
        return fila

    def _fila_neta(self, ws: Worksheet, fila: int, etiqueta: str, fila_base: int, fila_devuelta: int) -> int:
        celda_etiqueta = ws.cell(row=fila, column=plantilla.COLUMNA_ETIQUETA_TOTAL, value=etiqueta)
        celda_etiqueta.font = estilos.FUENTE_TOTAL_ETIQUETA
        celda_etiqueta.alignment = estilos.ALINEACION_DATO
        for columna in (
            plantilla.COLUMNA_IVA,
            plantilla.COLUMNA_TOTAL_NETO,
            plantilla.COLUMNA_TOTAL,
            plantilla.COLUMNA_OTROS,
        ):
            letra = get_column_letter(columna)
            celda = ws.cell(row=fila, column=columna, value=f"={letra}{fila_base}-{letra}{fila_devuelta}")
            celda.font = estilos.FUENTE_TOTAL_VALOR
            celda.number_format = estilos.FORMATO_MONEDA
            celda.fill = estilos.RELLENO_CLARO
        return fila + 1

    def _fila_documento(
        self,
        ws: Worksheet,
        fila: int,
        documento: DocumentoElectronico,
        *,
        marcas: bool,
        verificados: frozenset[str],
    ) -> None:
        self._escribir_documento(ws, fila, documento, marcas=marcas, verificados=verificados)

    def _escribir_documento(
        self,
        ws: Worksheet,
        fila: int,
        documento: DocumentoElectronico,
        *,
        marcas: bool,
        verificados: frozenset[str] = frozenset(),
    ) -> None:
        if marcas:
            valores_marca = (
                (1, True),
                (2, documento.cufe in verificados),
            )
            for columna, valor in valores_marca:
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
            f"=R{fila}-P{fila}-U{fila}",
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

        celda_otros = ws.cell(
            row=fila, column=plantilla.COLUMNA_OTROS, value=_numero(documento.impuestos_otros)
        )
        celda_otros.font = estilos.FUENTE_DATO_MONETARIO
        celda_otros.number_format = estilos.FORMATO_MONEDA
        celda_otros.fill = estilos.RELLENO_CLARO
        celda_otros.alignment = estilos.ALINEACION_DATO

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
            plantilla.COLUMNA_OTROS,
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
