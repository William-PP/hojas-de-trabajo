"""Editor gráfico de las reglas tributarias (`reglas/[año].yaml`).

Pensado para que el usuario pueda cambiar UVT, bases mínimas y tarifas sin editar YAML a mano.
También permite **cargar** un YAML que ya tenga (por ejemplo, el que le entregó su contador):
lo valida y lo muestra; al guardar, queda en `reglas/[año].yaml`.
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
    """Formulario para editar y guardar la configuración tributaria de un año."""

    def __init__(self, directorio_reglas: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.directorio_reglas = Path(directorio_reglas)
        self.setWindowTitle("Configuración tributaria (UVT, bases y tarifas)")

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
        self.btn_cargar = QPushButton("Cargar YAML existente…")
        self.btn_cargar.clicked.connect(self._on_cargar)
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.clicked.connect(self._on_guardar)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.close)

        self._construir_ui()
        self._cargar_anio_si_existe(self.campo_anio.value())

    # --- UI ---------------------------------------------------------------------------

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Estos datos salen del YAML del año. Si no los tienes, pídeselos a tu contador: "
                "la aplicación no los inventa."
            )
        )

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
        fila.addWidget(self.btn_guardar, 0, 1)
        fila.addWidget(self.btn_cerrar, 0, 2)
        fila.setColumnStretch(3, 1)
        layout.addWidget(acciones)

        layout.addWidget(self._estado)
        self.resize(640, 420)

    # --- Lectura y escritura ----------------------------------------------------------

    @property
    def ruta_anio(self) -> Path:
        return self.directorio_reglas / f"{self.campo_anio.value()}.yaml"

    def cargar_archivo(self, ruta: Path) -> ConfiguracionTributaria:
        """Carga un YAML existente en el formulario (sin copiarlo todavía)."""
        configuracion = cargar_desde_archivo(ruta, self.campo_anio.value())
        self._mostrar(configuracion)
        self._estado.setText(f"Cargado: {Path(ruta).name}. Revisa y guarda si corresponde.")
        return configuracion

    def guardar(self) -> Path:
        """Valida el formulario y escribe `reglas/[año].yaml`."""
        ruta = guardar_configuracion(
            self.campo_anio.value(),
            self.ruta_anio,
            uvt_pesos=self.campo_uvt.text(),
            conceptos=self._conceptos_del_formulario(),
        )
        self._estado.setText(f"Guardado en {ruta}")
        return ruta

    def _conceptos_del_formulario(self) -> dict[str, dict[str, str]]:
        return {
            concepto: {
                "base_minima_uvt": self._texto_celda(fila, 1),
                "tarifa": self._texto_celda(fila, 2),
            }
            for fila, concepto in enumerate(CONCEPTOS)
        }

    def _texto_celda(self, fila: int, columna: int) -> str:
        item = self.tabla.item(fila, columna)
        return item.text().strip() if item is not None else ""

    def _mostrar(self, configuracion: ConfiguracionTributaria) -> None:
        self.campo_anio.blockSignals(True)
        self.campo_anio.setValue(configuracion.anio)
        self.campo_anio.blockSignals(False)
        self.campo_uvt.setText(_texto_decimal(configuracion.uvt_pesos))
        for fila, concepto in enumerate(CONCEPTOS):
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
        for fila in range(len(CONCEPTOS)):
            self.tabla.setItem(fila, 1, QTableWidgetItem(""))
            self.tabla.setItem(fila, 2, QTableWidgetItem(""))

    # --- Acciones ---------------------------------------------------------------------

    def _cargar_anio_si_existe(self, anio: int) -> None:
        ruta = self.directorio_reglas / f"{anio}.yaml"
        if not ruta.is_file():
            self._limpiar()
            self._estado.setText(
                f"No existe {ruta.name}. Completa los datos y guarda para crearlo."
            )
            return
        try:
            configuracion = cargar_desde_archivo(ruta, anio)
        except ErrorConfiguracion as exc:
            self._limpiar()
            self._estado.setText(f"No se pudo leer {ruta.name}: {exc}")
            return
        self._mostrar(configuracion)
        self._estado.setText(f"Cargado: {ruta.name}")

    def _on_anio_cambiado(self, anio: int) -> None:
        self._cargar_anio_si_existe(anio)

    def _on_cargar(self) -> None:
        ruta, _filtro = QFileDialog.getOpenFileName(
            self,
            "Cargar configuración tributaria",
            str(self.directorio_reglas),
            "YAML (*.yaml *.yml)",
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
