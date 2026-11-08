"""Guía de los datos tributarios del año (los que entrega el contador).

La app guarda estos datos por dentro en un archivo técnico; el usuario no tiene que
saber qué es ni editarlo a mano. Aquí solo escribe tres cosas: la UVT del año y, por
cada concepto, la base mínima y la tarifa. Todo viene del contador o de la norma del
año; la aplicación no inventa valores.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dian_hojas.reglas.configuracion import (
    CONCEPTOS,
    ConfiguracionTributaria,
    ErrorConfiguracion,
    cargar_desde_archivo,
    guardar_configuracion,
)


class DialogoConfiguracionTributaria(QDialog):
    """Formulario guiado: solo hay que escribir los datos que da el contador."""

    def __init__(self, directorio_reglas: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.directorio_reglas = Path(directorio_reglas)
        self.setWindowTitle("Datos tributarios del año (los que da tu contador)")

        self.campo_anio = QSpinBox()
        self.campo_anio.setRange(2000, 2100)
        self.campo_anio.setValue(2026)
        self.campo_anio.valueChanged.connect(self._on_anio_cambiado)

        self.campo_uvt = QLineEdit()
        self.campo_uvt.setPlaceholderText("Valor de la UVT en pesos, p. ej. 220000")

        self.tabla = QTableWidget(len(CONCEPTOS), 3)
        self.tabla.setHorizontalHeaderLabels(
            ["Concepto", "Base mínima (UVT)", "Tarifa (decimal, 0.05 = 5%)"]
        )
        for fila, concepto in enumerate(CONCEPTOS):
            etiqueta = QTableWidgetItem(concepto)
            etiqueta.setFlags(etiqueta.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(fila, 0, etiqueta)
            self.tabla.setItem(fila, 1, QTableWidgetItem(""))
            self.tabla.setItem(fila, 2, QTableWidgetItem(""))
        self.tabla.resizeColumnsToContents()

        self._estado = QLabel("")
        self.btn_cargar = QPushButton("Cargar datos de tu contador…")
        self.btn_cargar.clicked.connect(self._on_cargar)
        self.btn_agregar = QPushButton("Añadir concepto…")
        self.btn_agregar.clicked.connect(self._on_agregar_concepto)
        self.btn_guardar = QPushButton("Guardar datos")
        self.btn_guardar.clicked.connect(self._on_guardar)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.close)

        self._construir_ui()
        self._cargar_anio_si_existe(self.campo_anio.value())

    # --- UI ---------------------------------------------------------------------------

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        guia = QLabel(
            "Guía en 3 pasos, sin tecnicismos:\n"
            "1) Pide a tu contador la UVT del año, las bases mínimas y las tarifas. "
            "La app no los inventa.\n"
            "2) Si tu contador te entrega un archivo con esos datos, usa el botón "
            "«Cargar datos de tu contador…».\n"
            "3) Si solo tienes los números en papel o en Excel, escríbelos abajo y pulsa «Guardar datos». "
            "La app los guarda sola por dentro."
        )
        guia.setWordWrap(True)
        layout.addWidget(guia)

        formulario = QWidget()
        grilla = QGridLayout(formulario)
        grilla.addWidget(QLabel("Año"), 0, 0)
        grilla.addWidget(self.campo_anio, 0, 1)
        grilla.addWidget(QLabel("UVT en pesos"), 1, 0)
        grilla.addWidget(self.campo_uvt, 1, 1)
        grilla.setColumnStretch(1, 1)
        layout.addWidget(formulario)

        layout.addWidget(self.tabla)

        acciones = QWidget()
        fila = QGridLayout(acciones)
        fila.addWidget(self.btn_cargar, 0, 0)
        fila.addWidget(self.btn_agregar, 0, 1)
        fila.addWidget(self.btn_guardar, 0, 2)
        fila.addWidget(self.btn_cerrar, 0, 3)
        fila.setColumnStretch(4, 1)
        layout.addWidget(acciones)

        layout.addWidget(self._estado)
        self.resize(640, 420)

    # --- Lectura y escritura ----------------------------------------------------------

    @property
    def ruta_anio(self) -> Path:
        return self.directorio_reglas / f"{self.campo_anio.value()}.yaml"

    def cargar_archivo(self, ruta: Path) -> ConfiguracionTributaria:
        """Carga un archivo de datos en el formulario (sin copiarlo todavía)."""
        configuracion = cargar_desde_archivo(ruta, self.campo_anio.value())
        self._mostrar(configuracion)
        self._estado.setText(f"Cargados los datos de «{Path(ruta).name}». Revísalos y pulsa «Guardar datos».")
        return configuracion

    def guardar(self) -> Path:
        """Valida el formulario y guarda los datos del año por dentro."""
        ruta = guardar_configuracion(
            self.campo_anio.value(),
            self.ruta_anio,
            uvt_pesos=self.campo_uvt.text(),
            conceptos=self._conceptos_del_formulario(),
        )
        self._estado.setText(f"Datos guardados para el año {self.campo_anio.value()}. Ya puedes cerrar.")
        return ruta

    def _conceptos_del_formulario(self) -> dict[str, dict[str, str]]:
        conceptos: dict[str, dict[str, str]] = {}
        for fila in range(self.tabla.rowCount()):
            concepto = self._texto_celda(fila, 0).strip().lower()
            if not concepto:
                continue
            conceptos[concepto] = {
                "base_minima_uvt": self._texto_celda(fila, 1),
                "tarifa": self._texto_celda(fila, 2),
            }
        for faltante in CONCEPTOS:
            if faltante not in conceptos:
                conceptos[faltante] = {"base_minima_uvt": "", "tarifa": ""}
        return conceptos

    def _nombres_conceptos(self) -> list[str]:
        nombres: list[str] = []
        for fila in range(self.tabla.rowCount()):
            nombre = self._texto_celda(fila, 0).strip()
            if nombre and nombre not in nombres:
                nombres.append(nombre)
        return nombres

    def agregar_concepto(self, nombre: str = "") -> None:
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        self.tabla.setItem(fila, 0, QTableWidgetItem(nombre))
        self.tabla.setItem(fila, 1, QTableWidgetItem(""))
        self.tabla.setItem(fila, 2, QTableWidgetItem(""))

    def _on_agregar_concepto(self) -> None:
        self.agregar_concepto()

    def _texto_celda(self, fila: int, columna: int) -> str:
        item = self.tabla.item(fila, columna)
        return item.text().strip() if item is not None else ""

    def _mostrar(self, configuracion: ConfiguracionTributaria) -> None:
        self.campo_anio.blockSignals(True)
        self.campo_anio.setValue(configuracion.anio)
        self.campo_anio.blockSignals(False)
        self.campo_uvt.setText(_texto_decimal(configuracion.uvt_pesos))
        nombres = list(CONCEPTOS) + sorted(
            n for n in configuracion.conceptos if n not in CONCEPTOS
        )
        # Asegura filas para todos los conceptos (base + extras).
        while self.tabla.rowCount() < len(nombres):
            self.agregar_concepto()
        for fila, concepto in enumerate(nombres):
            item = self.tabla.item(fila, 0)
            if item is None:
                self.tabla.setItem(fila, 0, QTableWidgetItem(concepto))
            else:
                item.setText(concepto)
            dato = configuracion.conceptos.get(concepto)
            self.tabla.setItem(
                fila,
                1,
                QTableWidgetItem(_texto_decimal(dato.base_minima_uvt) if dato else ""),
            )
            self.tabla.setItem(
                fila,
                2,
                QTableWidgetItem(_texto_decimal(dato.tarifa) if dato else ""),
            )

    def _limpiar(self) -> None:
        self.campo_uvt.clear()
        for fila in range(self.tabla.rowCount()):
            self.tabla.setItem(fila, 1, QTableWidgetItem(""))
            self.tabla.setItem(fila, 2, QTableWidgetItem(""))

    # --- Acciones ---------------------------------------------------------------------

    def _cargar_anio_si_existe(self, anio: int) -> None:
        ruta = self.directorio_reglas / f"{anio}.yaml"
        if not ruta.is_file():
            self._limpiar()
            self._estado.setText(
                f"Todavía no hay datos guardados para el año {anio}. "
                "Completa los datos que te dio tu contador y pulsa «Guardar datos»."
            )
            return
        try:
            configuracion = cargar_desde_archivo(ruta, anio)
        except ErrorConfiguracion as exc:
            self._limpiar()
            self._estado.setText(f"No se pudieron leer los datos guardados del año {anio}: {exc}")
            return
        self._mostrar(configuracion)
        self._estado.setText(f"Datos del año {anio} ya guardados. Revísalos si quieres cambiarlos.")

    def _on_anio_cambiado(self, anio: int) -> None:
        self._cargar_anio_si_existe(anio)

    def _on_cargar(self) -> None:
        ruta, _filtro = QFileDialog.getOpenFileName(
            self,
            "Cargar datos que te dio tu contador",
            str(self.directorio_reglas),
            "Datos tributarios (*.yaml *.yml);;Todos los archivos (*)",
        )
        if not ruta:
            return
        try:
            self.cargar_archivo(Path(ruta))
        except ErrorConfiguracion as exc:
            self._estado.setText(f"No se pudo cargar: {exc}")

    def _on_guardar(self) -> None:
        try:
            self.guardar()
        except ErrorConfiguracion as exc:
            self._estado.setText(f"No se guardó: {exc}")


def _texto_decimal(valor: Decimal) -> str:
    """Sin notación científica ni ceros de más: 220000 y 0.05 se muestran tal cual."""
    texto = format(valor, "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto
