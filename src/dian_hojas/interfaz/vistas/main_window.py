"""Ventana principal de la interfaz: formulario, resumen de cuadres y exportación."""

from __future__ import annotations

from pathlib import Path
from decimal import Decimal

from PySide6.QtCore import QStandardPaths, QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

from dian_hojas.aplicacion.exportar_hoja import ExportacionBloqueada, exportar_hoja
from dian_hojas.aplicacion.procesar_mes import ResultadoProcesamiento
from dian_hojas.aplicacion.sugerir_retefuente import sugerir_retefuente
from dian_hojas.dominio.enums import Categoria
from dian_hojas.dominio.modelos import Cliente, PerfilCliente, Periodo
from dian_hojas.dominio.retefuente import RetefuenteMes
from dian_hojas.dominio.soportes import documentos_en_texto
from dian_hojas.interfaz.viewmodels.procesar import HiloProcesar
from dian_hojas.interfaz.vistas.configuracion import DialogoConfiguracionTributaria
from dian_hojas.infraestructura.config_yaml import ConfigYaml
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl
from dian_hojas.infraestructura.ocr import ErrorOcr, Ocr
from dian_hojas.infraestructura.repo_sqlite import RepoSqlite
from dian_hojas.rutas import directorio_datos, directorio_reglas

CODIGOS_CUADRES = (
    ("C1", "Cantidad de documentos"),
    ("C2", "Total de los bloques contra la DIAN"),
    ("C3", "CUFE único"),
    ("C4", "Cuadre entre pestañas"),
    ("C5", "Fechas dentro del periodo"),
    ("C6", "El cliente está en el listado"),
    ("C7", "Solo IVA como impuesto"),
)


class VentanaPrincipal(QMainWindow):
    """Interfaz fina: formulario, resumen de cuadres y exportación.

    Toda la lógica vive en los casos de uso (`procesar_mes`, `exportar_hoja`); la ventana solo
    recoge lo que esos casos devuelven y muestra. No contiene reglas de negocio.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hojas de trabajo DIAN — retención en la fuente")

        self._proceso: ResultadoProcesamiento | None = None
        self._cliente: Cliente | None = None
        self._periodo: Periodo | None = None
        self._error: str | None = None
        self._hilo_procesar: QThread | None = None
        self._trabajo: HiloProcesar | None = None
        self._hilos: list[QThread] = []
        self._generacion = 0
        self._ultima_carpeta = ""
        self._soportes_verificados: set[str] = set()
        self._ocr = Ocr()
        self._estado = QLabel("Ningún mes procesado todavía.")
        self._estado.setWordWrap(True)
        self._estado.setMinimumHeight(28)
        self._etiquetas: dict[str, QLabel] = {}
        self._lista_no_clasificados = QListWidget()
        self._tabla_retefuente = QTableWidget()
        self.btn_confirmar_retefuente = QPushButton("Confirmar retenciones y exportar")
        self.btn_confirmar_retefuente.clicked.connect(self._on_btn_confirmar_retefuente)
        self.btn_confirmar_retefuente.setEnabled(False)
        self._tabla_retefuente.itemChanged.connect(self._on_tabla_retefuente_changed)
        self._config = ConfigYaml(directorio_reglas())
        self._repo = RepoSqlite(directorio_datos() / "retefuente.sqlite")
        self._construir_ui()
        self._cargar_perfiles()
        self._refrescar()

    # --- UI -----------------------------------------------------------------------

    def _construir_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.addWidget(self._formulario())
        layout.addWidget(self._resumen())
        layout.addWidget(self._tabla_retefuente)
        layout.addWidget(self.btn_confirmar_retefuente)
        layout.addWidget(self._estado)

    def _formulario(self) -> QWidget:
        contenedor = QWidget()
        layout = QGridLayout(contenedor)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        layout.addWidget(QLabel("Listado DIAN (Excel descargado)"), 0, 0)
        self._campo_ruta = QLineEdit()
        self._campo_ruta.setPlaceholderText(
            "El Excel que descargaste de la DIAN (tu hoja .xlsm también sirve: tiene la pestaña Dian)"
        )
        layout.addWidget(self._campo_ruta, 0, 1, 1, 2)
        boton_ruta = QPushButton("Examinar…")
        boton_ruta.clicked.connect(self._examinar_archivo)
        layout.addWidget(boton_ruta, 0, 3)

        layout.addWidget(QLabel("Año"), 1, 0)
        self._campo_anio = QSpinBox()
        self._campo_anio.setRange(2000, 2100)
        self._campo_anio.setValue(2026)
        layout.addWidget(self._campo_anio, 1, 1)
        layout.addWidget(QLabel("Mes"), 1, 2)
        self._campo_mes = QComboBox()
        self._campo_mes.addItems([str(m) for m in range(1, 13)])
        layout.addWidget(self._campo_mes, 1, 3)

        layout.addWidget(QLabel("Cliente guardado"), 2, 0)
        self.combo_perfiles = QComboBox()
        self.combo_perfiles.currentIndexChanged.connect(self._on_perfil_cambiado)
        layout.addWidget(self.combo_perfiles, 2, 1, 1, 2)
        self.btn_guardar_perfil = QPushButton("Guardar cliente")
        self.btn_guardar_perfil.clicked.connect(self._guardar_perfil)
        layout.addWidget(self.btn_guardar_perfil, 2, 3)

        layout.addWidget(QLabel("Nombre del cliente"), 3, 0)
        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre del cliente")
        layout.addWidget(self._campo_nombre, 3, 1)
        layout.addWidget(QLabel("Tipo"), 3, 2)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["NIT", "CC"])
        layout.addWidget(self.combo_tipo, 3, 3)
        layout.addWidget(QLabel("NIT / CC del cliente"), 4, 0)
        self._campo_nit = QLineEdit()
        self._campo_nit.setPlaceholderText("NIT o cédula (sin puntos ni DV)")
        layout.addWidget(self._campo_nit, 4, 1)
        layout.addWidget(QLabel("Carpeta de salida"), 4, 2)
        self._campo_carpeta = QLineEdit()
        self._campo_carpeta.setText(str(Path.home() / "Documents" / "Hojas_trabajo" / "salidas"))
        layout.addWidget(self._campo_carpeta, 4, 3)

        self.btn_procesar = QPushButton("Procesar")
        self.btn_procesar.clicked.connect(self._on_btn_procesar)
        self.btn_exportar = QPushButton("Exportar hoja de trabajo")
        self.btn_exportar.clicked.connect(self._on_btn_exportar)
        self.btn_exportar.setEnabled(False)
        self.check_otros = QCheckBox("Entiendo la diferencia y quiero exportar")
        self.check_otros.setEnabled(False)
        self.check_otros.toggled.connect(lambda _checked: self._refrescar())
        self.btn_configuracion = QPushButton("Datos tributarios (contador)…")
        self.btn_configuracion.clicked.connect(self._on_btn_configuracion)
        self.btn_verificar_soportes = QPushButton("Verificar soportes (OCR, opcional)…")
        self.btn_verificar_soportes.clicked.connect(self._on_btn_verificar_soportes)
        layout.addWidget(self.btn_procesar, 5, 0)
        layout.addWidget(self.btn_exportar, 5, 1)
        layout.addWidget(self.btn_configuracion, 5, 2)
        layout.addWidget(self.btn_verificar_soportes, 5, 3)
        layout.addWidget(self.check_otros, 6, 0, 1, 4)

        return contenedor

    # --- Perfiles por cliente (Fase 4) -------------------------------------------------

    def _cargar_perfiles(self) -> None:
        """Llena el combo con los clientes recordados y, si hay uno, lo pone en el formulario."""
        self.combo_perfiles.blockSignals(True)
        self.combo_perfiles.clear()
        perfiles = self._repo.perfiles()
        if not perfiles:
            self.combo_perfiles.addItem("— Nuevo cliente —", None)
        else:
            for perfil in perfiles:
                etiqueta = f"{perfil.cliente.nombre} ({perfil.cliente.numero})"
                self.combo_perfiles.addItem(etiqueta, perfil.cliente.numero)
        self.combo_perfiles.blockSignals(False)
        if len(perfiles) == 1:
            self._on_perfil_cambiado(0)

    def _guardar_perfil(self) -> None:
        """Guarda el cliente actual para no volver a escribirlo cada mes."""
        nit = self._campo_nit.text().strip()
        nombre = self._campo_nombre.text().strip()
        if not nit or not nombre:
            self._estado.setText("Para guardar el cliente necesito su nombre y su NIT.")
            return
        perfil = PerfilCliente(
            cliente=Cliente(
                nombre=nombre,
                tipo_identificacion=self.combo_tipo.currentText() if hasattr(self, "combo_tipo") else "NIT",
                numero=nit,
            ),
            carpeta_salida=self._campo_carpeta.text().strip(),
        )
        self._repo.guardar_perfil(perfil)
        self._cargar_perfiles()
        indice = self.combo_perfiles.findData(nit)
        if indice >= 0:
            self.combo_perfiles.blockSignals(True)
            self.combo_perfiles.setCurrentIndex(indice)
            self.combo_perfiles.blockSignals(False)
        self._estado.setText(f"Cliente guardado: {nombre}.")

    def _on_perfil_cambiado(self, indice: int) -> None:
        numero = self.combo_perfiles.itemData(indice)
        if not numero:
            return
        perfil = self._repo.perfil(str(numero))
        if perfil is None:
            return
        self._campo_nombre.setText(perfil.cliente.nombre)
        self._campo_nit.setText(perfil.cliente.numero)
        if hasattr(self, "combo_tipo"):
            self.combo_tipo.setCurrentText(perfil.cliente.tipo_identificacion)
        if perfil.carpeta_salida:
            self._campo_carpeta.setText(perfil.carpeta_salida)

    def _on_btn_configuracion(self) -> None:
        dialogo = DialogoConfiguracionTributaria(self._config.directorio_reglas, self)
        dialogo.exec()
        if self._proceso is not None:
            self._llenar_tabla_retefuente()

    def _examinar_archivo(self) -> None:
        ruta, _filtro = QFileDialog.getOpenFileName(
            self,
            "Listado de la DIAN",
            self._carpeta_inicial(),
            "Todos los archivos (*);;Listados Excel (*.xlsx *.xlsm *.xls)",
        )
        if not ruta:
            return
        archivo = Path(ruta)
        self._ultima_carpeta = str(archivo.parent)
        self._campo_ruta.setText(ruta)
        if archivo.suffix.lower() == ".xls":
            self._estado.setText(
                "Ese archivo es .xls (formato antiguo). Ábrelo en Excel y guárdalo como .xlsx "
                "para poder procesarlo."
            )

    def _carpeta_inicial(self) -> str:
        """Abre el diálogo en la última carpeta usada o, si no, en Descargas (Windows)."""
        if self._ultima_carpeta and Path(self._ultima_carpeta).is_dir():
            return self._ultima_carpeta
        carpeta = _carpeta_descargas()
        return str(carpeta if carpeta.is_dir() else Path.home())

    def _resumen(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(4, 4, 4, 4)

        for codigo, titulo in CODIGOS_CUADRES:
            etiqueta = QLabel(f"{codigo} — {titulo}: —")
            etiqueta.setObjectName(f"cuadre-{codigo}")
            etiqueta.setWordWrap(True)
            etiqueta.setMinimumHeight(28)
            self._etiquetas[codigo] = etiqueta
            layout.addWidget(etiqueta)

        layout.addWidget(QLabel("Documentos sin clasificar"))
        self._lista_no_clasificados = QListWidget()
        self._lista_no_clasificados.setMaximumHeight(90)
        layout.addWidget(self._lista_no_clasificados)

        return contenedor

    @property
    def tabla_retefuente(self) -> QTableWidget:
        """La tabla editable de retención: solo lectura de la vista, sin lógica de negocio."""
        return self._tabla_retefuente

    @property
    def trabajo(self) -> HiloProcesar | None:
        """El trabajador actual del hilo; útil para esperar sus señales en las pruebas."""
        return self._trabajo

    @property
    def soportes_verificados(self) -> frozenset[str]:
        """CUFEs cuyo soporte físico el usuario ya cruzó con OCR (opcional)."""
        return frozenset(self._soportes_verificados)

    # --- Estado -------------------------------------------------------------------

    def _refrescar(self) -> None:
        if self._proceso is None:
            self.btn_exportar.setEnabled(False)
            self._estado.setText(self._error or "Ningún mes procesado todavía.")
        else:
            requiere = self._proceso.requiere_confirmacion_otros
            confirmado = getattr(self, "check_otros", None)
            chequeado = bool(confirmado and confirmado.isChecked())
            habilitado = (
                not self._proceso.mes_vacio
                and self._proceso.puede_exportar
                and self._error is None
                and ((not requiere) or chequeado)
            )
            self.btn_exportar.setEnabled(habilitado)
            resumen = (
                "Mes procesado: "
                f"{self._proceso.filas_dian} documentos, "
                f"total {self._proceso.total_dian}"
            )
            if self._error is not None:
                resumen = self._error
            elif self._proceso.mes_vacio:
                resumen += ". No hay documentos que puedan ir a las hojas."
            elif not self._proceso.puede_exportar:
                fallidos = ", ".join(c.codigo for c in self._proceso.cuadres_fallidos)
                resumen += f". Revisa los cuadres en rojo ({fallidos}) antes de exportar."
            elif requiere and not chequeado:
                resumen += ". Hay otros impuestos (C7 en amarillo): marca la casilla para exportar."
            self._estado.setText(resumen)

        if self._proceso is None:
            if hasattr(self, "check_otros"):
                self.check_otros.setEnabled(False)
            for codigo, titulo in CODIGOS_CUADRES:
                self._etiquetas[codigo].setText(f"{codigo} — {titulo}: sin procesar")
            self._lista_no_clasificados.clear()
            return

        if hasattr(self, "check_otros"):
            self.check_otros.setEnabled(self._proceso.requiere_confirmacion_otros)

        for codigo, titulo in CODIGOS_CUADRES:
            cuadre = next((c for c in self._proceso.cuadres if c.codigo == codigo), None)
            if cuadre is None:
                estado = "—"
            elif cuadre.ok:
                estado = "OK"
            elif not cuadre.bloqueante:
                estado = "ALERTA"
            else:
                estado = "FALLA"
            detalle = cuadre.detalle if cuadre is not None else "sin ejecutar"
            self._etiquetas[codigo].setText(f"{codigo} — {titulo}: {estado}. {detalle}")

        self._lista_no_clasificados.clear()
        for documento in self._proceso.resultado.no_clasificados:
            self._lista_no_clasificados.addItem(f"{documento.prefijo + '-' if documento.prefijo else ''}{documento.folio}")

        self._llenar_tabla_retefuente()

    # --- Retención -----------------------------------------------------------------

    def _compras_del_proceso(self):
        if self._proceso is None:
            return ()
        return tuple(
            d
            for d in self._proceso.resultado.documentos
            if d.categoria is Categoria.COMPRA
        )

    def _llenar_tabla_retefuente(self) -> None:
        """Puebla la tabla editable con las sugerencias de retención del mes (si las hay)."""
        self._tabla_retefuente.setRowCount(0)
        self._tabla_retefuente.setColumnCount(8)
        self._tabla_retefuente.setHorizontalHeaderLabels(
            [
                "CUFE",
                "Proveedor (NIT)",
                "Concepto",
                "Base",
                "Base mínima (UVT)",
                "¿Supera?",
                "Retención",
                "Observaciones",
            ]
        )
        if self._proceso is None:
            return
        compras = self._compras_del_proceso()
        if not compras:
            return
        try:
            sugerencia = sugerir_retefuente(
                compras,
                self._config.configuracion(self._periodo.anio if self._periodo else 2026),
                self._repo,
            )
        except Exception as exc:  # pragma: no cover - el bloque de retención no debe tumbar la vista
            self._estado.setText(f"No se pudieron calcular las retenciones: {exc}")
            return

        for linea in sugerencia.lineas:
            fila = self._tabla_retefuente.rowCount()
            self._tabla_retefuente.insertRow(fila)
            valores = (
                linea.documento.cufe if linea.documento else "",
                linea.documento.nit_emisor if linea.documento else "",
                linea.concepto,
                float(linea.base),
                float(linea.base_minima_uvt),
                "Sí" if linea.supera_base else "No",
                float(linea.retencion),
                f"Proveedor {linea.documento.nit_emisor}" if linea.documento else "",
            )
            for columna, valor in enumerate(valores):
                self._tabla_retefuente.setItem(fila, columna, QTableWidgetItem(str(valor)))

    def _on_tabla_retefuente_changed(self, cambio) -> None:
        """La edición de la tabla habilita la acción de confirmar."""
        self.btn_confirmar_retefuente.setEnabled(True)

    def _calcular_retefuente(self) -> RetefuenteMes:
        """Calcula las retenciones sugeridas del mes procesado (decisión persistida incluida)."""
        if self._proceso is None or self._periodo is None:
            raise ValueError("No hay un mes procesado para retener.")
        compras = self._compras_del_proceso()
        if not compras:
            return RetefuenteMes(lineas=(), total_retencion=Decimal("0"))
        return sugerir_retefuente(
            compras,
            self._config.configuracion(self._periodo.anio),
            self._repo,
        )

    def _on_btn_confirmar_retefuente(self) -> None:
        """Confirma las retenciones sugeridas, persiste y exporta la hoja con ellas."""
        if self._proceso is None or self._periodo is None:
            return
        if not self._compras_del_proceso():
            self._estado.setText("No hay compras para retener en este mes.")
            return
        try:
            retefuente = self._calcular_retefuente()
        except Exception as exc:
            self._estado.setText(f"No se pudo calcular la retención: {exc}")
            return
        filas = self._tabla_retefuente.rowCount()
        for indice, linea in enumerate(retefuente.lineas):
            if linea.documento is None or indice >= filas:
                continue
            item = self._tabla_retefuente.item(indice, 2)
            concepto_elegido = (
                item.text().strip() if item is not None and item.text().strip() else linea.concepto
            )
            self._repo.asignar_concepto(linea.documento.nit_emisor, concepto_elegido)
        # Re-sugiere con las decisiones persistidas y exporta con el resultado confirmado.
        try:
            retefuente = self._calcular_retefuente()
        except Exception as exc:
            self._estado.setText(f"No se pudieron recalcular las retenciones: {exc}")
            return
        try:
            exportar_hoja(
                self._proceso,
                self._cliente or Cliente(nombre="Cliente", numero="0"),
                self._periodo,
                Path(self._campo_carpeta.text()),
                EscritorOpenpyxl(),
                retefuente=retefuente,
                soportes_verificados=self.soportes_verificados,
                confirmar_otros_impuestos=self.check_otros.isChecked() if hasattr(self, "check_otros") else False,
                # El botón ya es la confirmación del usuario: no debe re-pedir.
                confirmar_pendientes=True,
            )
        except ExportacionBloqueada as exc:
            self._error = str(exc)
            self._estado.setText(f"No se pudo exportar: {exc}")
        else:
            self._error = None
            self._estado.setText(f"Retenciones confirmadas y exportadas. Retención total: {retefuente.total_retencion}")

    # --- Soportes físicos opcionales (Fase 4) ------------------------------------------

    def _on_btn_verificar_soportes(self) -> None:
        if self._proceso is None:
            self._estado.setText("Primero procesa un mes para poder verificar soportes.")
            return
        rutas, _filtro = QFileDialog.getOpenFileNames(
            self,
            "Soportes físicos (PDF o imagen)",
            "",
            "Soportes (*.pdf *.png *.jpg *.jpeg *.tif *.tiff);;Todos los archivos (*)",
        )
        if rutas:
            self.verificar_soportes([Path(ruta) for ruta in rutas])

    def verificar_soportes(self, rutas: list[Path]) -> tuple:
        """Intenta leer los soportes y marca los documentos que aparecen en su texto.

        Es opcional: si el OCR no está instalado o un archivo no se puede leer, se avisa y se
        sigue. Nada de esto bloquea la exportación.
        """
        if self._proceso is None:
            self._estado.setText("Primero procesa un mes para poder verificar soportes.")
            return ()

        encontrados = []
        avisos: list[str] = []
        for ruta in rutas:
            try:
                texto = self._ocr.extraer_texto(Path(ruta))
            except ErrorOcr as exc:
                avisos.append(str(exc))
                continue
            documentos = documentos_en_texto(texto, self._proceso.resultado.documentos)
            encontrados.extend(documentos)
            self._soportes_verificados.update(documento.cufe for documento in documentos)

        if not encontrados and avisos:
            self._estado.setText("No se pudo verificar ningún soporte. " + " ".join(avisos))
        else:
            mensaje = (
                f"Soportes verificados: {len(encontrados)} documento(s) "
                f"en {len(rutas)} archivo(s)."
            )
            if avisos:
                mensaje += " Avisos: " + " ".join(avisos)
            self._estado.setText(mensaje)
        return tuple(encontrados)

    # --- Procesamiento ------------------------------------------------------------

    def _parar_hilo(self) -> None:
        """Detiene el procesamiento anterior antes de lanzar otro.

        Sin esto, el hilo viejo sigue trabajando y su resultado llega tarde. Las señales llevan un
        número de generación, así que ese resultado viejo se descarta; aquí solo se le pide al hilo
        anterior que termine y se espera un poco. Si no alcanza (archivo muy grande) queda vivo en
        `_hilos` hasta que su propio `finished` lo suelte, para que Qt no lo destruya en marcha.
        """
        hilo = self._hilo_procesar
        self._trabajo = None
        self._hilo_procesar = None
        if hilo is not None and hilo.isRunning():
            hilo.quit()
            hilo.wait(3000)

    def _soltar_hilo(self, hilo: QThread) -> None:
        if hilo in self._hilos:
            self._hilos.remove(hilo)

    def _on_btn_procesar(self) -> None:
        ruta = Path(self._campo_ruta.text())
        anio = self._campo_anio.value()
        mes = int(self._campo_mes.currentText())
        periodo = Periodo(anio=anio, mes=mes)
        nit = self._campo_nit.text().strip()
        nombre = self._campo_nombre.text().strip() or f"Cliente {nit}"
        tipo = self.combo_tipo.currentText() if hasattr(self, "combo_tipo") else "NIT"
        cliente = Cliente(nombre=nombre, tipo_identificacion=tipo, numero=nit) if nit else None
        if cliente is None:
            self._estado.setText("Ingresa el NIT del cliente para procesar.")
            return
        self._cliente = cliente
        self._periodo = periodo
        self.procesar(ruta, cliente, periodo)

    def procesar(self, ruta: Path, cliente: Cliente, periodo: Periodo) -> None:
        """Lanza el procesamiento en un QThread y refresca la vista al terminar."""
        self._parar_hilo()
        self._proceso = None
        self._error = None
        self._soportes_verificados.clear()
        self._refrescar()
        self._estado.setText("Procesando el listado…")
        self.btn_procesar.setEnabled(False)
        self._generacion += 1
        trabajo = HiloProcesar(ruta, cliente, periodo, generacion=self._generacion)
        hilo = QThread()
        trabajo.moveToThread(hilo)
        trabajo.termino_generacion.connect(self._on_termino)
        trabajo.error_generacion.connect(self._on_error)
        trabajo.finished.connect(hilo.quit)
        hilo.finished.connect(lambda: self._soltar_hilo(hilo))
        hilo.started.connect(trabajo.trabajar)
        self._hilo_procesar = hilo
        self._trabajo = trabajo
        self._hilos.append(hilo)
        hilo.start()

    def _on_termino(self, resultado: ResultadoProcesamiento | None, generacion: int) -> None:
        if generacion != self._generacion:
            return
        if resultado is None:
            if self._error is None:
                self._error = "El listado no se pudo procesar: revisa la ruta y los datos."
        else:
            self._proceso = resultado
            self._error = None
            self._soportes_verificados.clear()
        self.btn_procesar.setEnabled(True)
        self._refrescar()

    def _on_error(self, mensaje: str, generacion: int) -> None:
        if generacion != self._generacion:
            return
        self._error = mensaje
        self.btn_procesar.setEnabled(True)
        self._refrescar()

    def closeEvent(self, evento) -> None:
        """Detiene los hilos antes de cerrar para no dejar procesos ni Qt a medias."""
        self._parar_hilo()
        for hilo in list(self._hilos):
            try:
                hilo.quit()
                hilo.wait(5000)
            except RuntimeError:
                pass
        self._hilos.clear()
        try:
            self._repo.cerrar()
        except Exception:
            pass
        super().closeEvent(evento)

    # --- Exportación ---------------------------------------------------------------

    def _on_btn_exportar(self) -> None:
        if self._proceso is None or self._cliente is None or self._periodo is None:
            return
        aviso = ""
        confirmar_pendientes = False
        try:
            retefuente = self._calcular_retefuente()
        except Exception as exc:
            retefuente = None
            aviso = (
                "Se exportó sin la pestaña Retefuente porque todavía no tienes los "
                f"datos tributarios del año: {exc}"
            )
        if retefuente is not None and retefuente.hay_pendientes:
            respuesta = QMessageBox.question(
                self,
                "Líneas pendientes de confirmar",
                f"Hay {retefuente.cantidad_pendientes} línea(s) pendientes de confirmar.\n\n"
                "¿Quieres exportar igualmente como PROVISIONAL?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return
            confirmar_pendientes = True
        try:
            ruta = exportar_hoja(
                self._proceso,
                self._cliente,
                self._periodo,
                Path(self._campo_carpeta.text()),
                EscritorOpenpyxl(),
                retefuente=retefuente,
                soportes_verificados=self.soportes_verificados,
                confirmar_otros_impuestos=self.check_otros.isChecked() if hasattr(self, "check_otros") else False,
                confirmar_pendientes=confirmar_pendientes,
            )
        except ExportacionBloqueada as exc:
            self._error = str(exc)
            self._estado.setText(f"No se pudo exportar: {exc}")
            return
        self._error = None
        mensaje = f"Exportado: {ruta.name}"
        if aviso:
            mensaje += f". {aviso}"
        self._estado.setText(mensaje)

    def exportar(self, carpeta: Path, confirmar_otros_impuestos: bool = False, confirmar_pendientes: bool = False) -> Path:
        """Exporta la hoja de trabajo. Lanza `ExportacionBloqueada` si hay cuadre fallido."""
        if self._proceso is None or self._cliente is None or self._periodo is None:
            raise ValueError("No hay un mes procesado para exportar.")
        return exportar_hoja(
            self._proceso,
            self._cliente,
            self._periodo,
            carpeta,
            EscritorOpenpyxl(),
            retefuente=self._calcular_retefuente(),
            soportes_verificados=self.soportes_verificados,
            confirmar_otros_impuestos=confirmar_otros_impuestos or (hasattr(self, "check_otros") and self.check_otros.isChecked()),
            confirmar_pendientes=confirmar_pendientes,
        )


def _carpeta_descargas() -> Path:
    """Devuelve la carpeta Descargas que maneja Windows (p. ej. `D:\\Downloads`).

    Usa `QStandardPaths.DownloadLocation`, el modo Qt de pedirle a Windows la carpeta
    real de descargas, y solo `pathlib`. No se usan rutas duras (`C:` ni `D:`).
    """
    carpeta = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    if carpeta:
        ruta = Path(carpeta)
        if ruta.is_dir():
            return ruta
    return Path.home()
