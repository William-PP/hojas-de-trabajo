"""Ventana principal de la interfaz: formulario, resumen de cuadres y exportación."""

from __future__ import annotations

from pathlib import Path
from decimal import Decimal

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QMainWindow,
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
        self._soportes_verificados: set[str] = set()
        self._ocr = Ocr()
        self._estado = QLabel("Ningún mes procesado todavía.")
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

        layout.addWidget(QLabel("Listado DIAN (.xlsx)"), 0, 0)
        self._campo_ruta = QLineEdit()
        self._campo_ruta.setPlaceholderText("Ruta del listado descargado de la DIAN")
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
        layout.addWidget(QLabel("NIT del cliente"), 3, 2)
        self._campo_nit = QLineEdit()
        self._campo_nit.setPlaceholderText("NIT del cliente")
        layout.addWidget(self._campo_nit, 3, 3)

        layout.addWidget(QLabel("Carpeta de salida"), 4, 0)
        self._campo_carpeta = QLineEdit()
        self._campo_carpeta.setText(str(Path.home() / "Documents" / "Hojas_trabajo" / "salidas"))
        layout.addWidget(self._campo_carpeta, 4, 1, 1, 3)

        self.btn_procesar = QPushButton("Procesar")
        self.btn_procesar.clicked.connect(self._on_btn_procesar)
        self.btn_exportar = QPushButton("Exportar hoja de trabajo")
        self.btn_exportar.clicked.connect(self._on_btn_exportar)
        self.btn_exportar.setEnabled(False)
        self.btn_configuracion = QPushButton("Configuración tributaria…")
        self.btn_configuracion.clicked.connect(self._on_btn_configuracion)
        self.btn_verificar_soportes = QPushButton("Verificar soportes (OCR, opcional)…")
        self.btn_verificar_soportes.clicked.connect(self._on_btn_verificar_soportes)
        layout.addWidget(self.btn_procesar, 5, 0)
        layout.addWidget(self.btn_exportar, 5, 1)
        layout.addWidget(self.btn_configuracion, 5, 2)
        layout.addWidget(self.btn_verificar_soportes, 5, 3)

        return contenedor

    # --- Perfiles por cliente (Fase 4) -------------------------------------------------

    def _cargar_perfiles(self) -> None:
        """Llena el combo con los clientes recordados; no cambia el formulario."""
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

    def _guardar_perfil(self) -> None:
        """Guarda el cliente actual para no volver a escribirlo cada mes."""
        nit = self._campo_nit.text().strip()
        nombre = self._campo_nombre.text().strip()
        if not nit or not nombre:
            self._estado.setText("Para guardar el cliente necesito su nombre y su NIT.")
            return
        perfil = PerfilCliente(
            cliente=Cliente(nombre=nombre, tipo_identificacion="NIT", numero=nit),
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
        if perfil.carpeta_salida:
            self._campo_carpeta.setText(perfil.carpeta_salida)

    def _on_btn_configuracion(self) -> None:
        dialogo = DialogoConfiguracionTributaria(self._config.directorio_reglas, self)
        dialogo.exec()
        if self._proceso is not None:
            self._llenar_tabla_retefuente()

    def _examinar_archivo(self) -> None:
        ruta, _filtro = QFileDialog.getOpenFileName(self, "Listado de la DIAN", "", "Excel (*.xlsx)")
        if ruta:
            self._campo_ruta.setText(ruta)

    def _resumen(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(4, 4, 4, 4)

        for codigo, titulo in CODIGOS_CUADRES:
            etiqueta = QLabel(f"{codigo} — {titulo}: —")
            etiqueta.setObjectName(f"cuadre-{codigo}")
            self._etiquetas[codigo] = etiqueta
            layout.addWidget(etiqueta)

        layout.addWidget(QLabel("Documentos sin clasificar"))
        self._lista_no_clasificados = QListWidget()
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
            self._estado.setText("Ningún mes procesado todavía.")
        else:
            habilitado = (
                not self._proceso.mes_vacio
                and self._proceso.puede_exportar
                and self._error is None
            )
            self.btn_exportar.setEnabled(habilitado)
            self._estado.setText(
                "Mes procesado: "
                f"{self._proceso.filas_dian} documentos, "
                f"total {self._proceso.total_dian}"
            )

        if self._proceso is None:
            for codigo, titulo in CODIGOS_CUADRES:
                self._etiquetas[codigo].setText(f"{codigo} — {titulo}: sin procesar")
            self._lista_no_clasificados.clear()
            return

        for codigo, titulo in CODIGOS_CUADRES:
            cuadre = next((c for c in self._proceso.cuadres if c.codigo == codigo), None)
            estado = "OK" if cuadre is not None and cuadre.ok else ("FALLA" if cuadre else "—")
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
        retefuente = self._calcular_retefuente()
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
        retefuente = self._calcular_retefuente()
        try:
            exportar_hoja(
                self._proceso,
                self._cliente or Cliente(nombre="Cliente", numero="0"),
                self._periodo,
                Path(self._campo_carpeta.text()),
                EscritorOpenpyxl(),
                retefuente=retefuente,
                soportes_verificados=self.soportes_verificados,
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
        if self._hilo_procesar is not None and self._hilo_procesar.isRunning():
            self._hilo_procesar.quit()
            self._hilo_procesar.wait(10000)

    def _on_btn_procesar(self) -> None:
        ruta = Path(self._campo_ruta.text())
        anio = self._campo_anio.value()
        mes = int(self._campo_mes.currentText())
        periodo = Periodo(anio=anio, mes=mes)
        nit = self._campo_nit.text().strip()
        nombre = self._campo_nombre.text().strip() or f"Cliente {nit}"
        cliente = Cliente(nombre=nombre, tipo_identificacion="NIT", numero=nit) if nit else None
        if cliente is None:
            self._estado.setText("Ingresa el NIT del cliente para procesar.")
            return
        self._cliente = cliente
        self._periodo = periodo
        self.procesar(ruta, cliente, periodo)

    def procesar(self, ruta: Path, cliente: Cliente, periodo: Periodo) -> None:
        """Lanza el procesamiento en un QThread y refresca la vista al terminar."""
        self._parar_hilo()
        trabajo = HiloProcesar(ruta, cliente, periodo)
        hilo = QThread()
        trabajo.moveToThread(hilo)
        trabajo.termino.connect(self._on_termino)
        trabajo.error.connect(self._on_error)
        trabajo.finished.connect(hilo.quit)
        hilo.finished.connect(hilo.deleteLater)
        hilo.started.connect(trabajo.trabajar)
        self._hilo_procesar = hilo
        self._trabajo = trabajo
        hilo.start()

    def _on_termino(self, resultado: ResultadoProcesamiento | None) -> None:
        if resultado is None:
            self._error = "El listado no se pudo procesar: revisa la ruta y los datos."
        else:
            self._proceso = resultado
            self._error = None
            self._soportes_verificados.clear()
        self._refrescar()

    def _on_error(self, mensaje: str) -> None:
        self._error = mensaje
        self._refrescar()

    # --- Exportación ---------------------------------------------------------------

    def _on_btn_exportar(self) -> None:
        if self._proceso is None or self._cliente is None or self._periodo is None:
            return
        try:
            retefuente = self._calcular_retefuente()
        except Exception as exc:
            self._error = str(exc)
            self._estado.setText(f"No se pudo calcular la retención: {exc}")
            return
        try:
            ruta = exportar_hoja(
                self._proceso,
                self._cliente,
                self._periodo,
                Path(self._campo_carpeta.text()),
                EscritorOpenpyxl(),
                retefuente=retefuente,
                soportes_verificados=self.soportes_verificados,
            )
        except ExportacionBloqueada as exc:
            self._error = str(exc)
            self._estado.setText(f"No se pudo exportar: {exc}")
            return
        self._error = None
        self._estado.setText(f"Exportado: {ruta.name}")

    def exportar(self, carpeta: Path) -> Path:
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
        )
