"""Ventana principal de la interfaz: formulario, resumen de cuadres y exportación."""

from __future__ import annotations

from pathlib import Path

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
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

from dian_hojas.aplicacion.exportar_hoja import ExportacionBloqueada, exportar_hoja
from dian_hojas.aplicacion.procesar_mes import ResultadoProcesamiento
from dian_hojas.dominio.modelos import Cliente, Periodo
from dian_hojas.interfaz.viewmodels.procesar import HiloProcesar
from dian_hojas.infraestructura.escritor_xlsx import EscritorOpenpyxl

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
        self._estado = QLabel("Ningún mes procesado todavía.")
        self._etiquetas: dict[str, QLabel] = {}

        self._construir_ui()
        self._refrescar()

    # --- UI -----------------------------------------------------------------------

    def _construir_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.addWidget(self._formulario())
        layout.addWidget(self._resumen())
        layout.addWidget(self._estado)

    def _formulario(self) -> QWidget:
        contenedor = QWidget()
        layout = QGridLayout(contenedor)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        layout.addWidget(QLabel("Listado DIAN (.xlsx)"), 0, 0)
        self._campo_ruta = QLineEdit()
        self._campo_ruta.setPlaceholderText("Ruta del listado descargado de la DIAN")
        layout.addWidget(self._campo_ruta, 0, 1)
        boton_ruta = QPushButton("Examinar…")
        boton_ruta.clicked.connect(self._examinar_archivo)
        layout.addWidget(boton_ruta, 0, 2)

        layout.addWidget(QLabel("Año"), 1, 0)
        self._campo_anio = QSpinBox()
        self._campo_anio.setRange(2000, 2100)
        self._campo_anio.setValue(2026)
        layout.addWidget(self._campo_anio, 1, 1)
        layout.addWidget(QLabel("Mes"), 1, 2)
        self._campo_mes = QComboBox()
        self._campo_mes.addItems([str(m) for m in range(1, 13)])
        layout.addWidget(self._campo_mes, 1, 3)

        layout.addWidget(QLabel("Nombre del cliente"), 2, 0)
        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre del cliente")
        layout.addWidget(self._campo_nombre, 2, 1)
        layout.addWidget(QLabel("NIT del cliente"), 2, 2)
        self._campo_nit = QLineEdit()
        self._campo_nit.setPlaceholderText("NIT del cliente")
        layout.addWidget(self._campo_nit, 2, 3)

        layout.addWidget(QLabel("Carpeta de salida"), 3, 0, 2, 1)
        self._campo_carpeta = QLineEdit()
        self._campo_carpeta.setText(str(Path.home() / "Documents" / "Hojas_trabajo" / "salidas"))
        layout.addWidget(self._campo_carpeta, 3, 1, 1, 3)

        self.btn_procesar = QPushButton("Procesar")
        self.btn_procesar.clicked.connect(self._on_btn_procesar)
        self.btn_exportar = QPushButton("Exportar hoja de trabajo")
        self.btn_exportar.clicked.connect(self._on_btn_exportar)
        self.btn_exportar.setEnabled(False)
        layout.addWidget(self.btn_procesar, 4, 0)
        layout.addWidget(self.btn_exportar, 4, 1)

        return contenedor

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
    def trabajo(self) -> HiloProcesar | None:
        """El trabajador actual del hilo; útil para esperar sus señales en las pruebas."""
        return self._trabajo

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
        self._refrescar()

    def _on_error(self, mensaje: str) -> None:
        self._error = mensaje
        self._refrescar()

    # --- Exportación ---------------------------------------------------------------

    def _on_btn_exportar(self) -> None:
        if self._proceso is None or self._cliente is None or self._periodo is None:
            return
        carpeta = Path(self._campo_carpeta.text())
        try:
            ruta = exportar_hoja(self._proceso, self._cliente, self._periodo, carpeta, EscritorOpenpyxl())
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
        return exportar_hoja(self._proceso, self._cliente, self._periodo, carpeta, EscritorOpenpyxl())
