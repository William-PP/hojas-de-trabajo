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
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
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
        self._snapshot_guardado = ""
        self._limpiando = False

        self.campo_anio = QSpinBox()
        self.campo_anio.setRange(2000, 2100)
        self.campo_anio.setValue(2026)
        self.campo_anio.valueChanged.connect(self._on_anio_cambiado)

        self.campo_uvt = QLineEdit()
        self.campo_uvt.setPlaceholderText("Valor oficial de la UVT del año")
        self.campo_fuente = QLineEdit()
        self.campo_fecha = QLineEdit()
        self.campo_fuente.setPlaceholderText("Opcional: quién validó (contador/norma)")
        self.campo_fecha.setPlaceholderText("Opcional: fecha de validación")

        self.tabla = QTableWidget(len(CONCEPTOS), 3)
        self.tabla.setHorizontalHeaderLabels(
            ["Concepto", "Base mínima (UVT)", "Tarifa (%)"]
        )
        for fila, concepto in enumerate(CONCEPTOS):
            etiqueta = QTableWidgetItem(concepto)
            etiqueta.setFlags(etiqueta.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(fila, 0, etiqueta)
            self.tabla.setItem(fila, 1, QTableWidgetItem(""))
            self.tabla.setItem(fila, 2, QTableWidgetItem(""))
        self.tabla.resizeColumnsToContents()
        self.tabla.horizontalHeader().setStretchLastSection(False)

        self._estado = QLabel("")
        self.btn_cargar = QPushButton("Cargar datos de tu contador…")
        self.btn_cargar.clicked.connect(self._on_cargar)
        self.btn_agregar = QPushButton("Agregar concepto")
        self.btn_agregar.clicked.connect(self._on_agregar_concepto)
        self.btn_quitar = QPushButton("Quitar concepto")
        self.btn_quitar.clicked.connect(self._on_quitar_concepto)
        self.btn_guardar = QPushButton("Guardar datos")
        self.btn_guardar.clicked.connect(self._on_guardar)
        self.btn_guardar.setDefault(True)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self._on_cerrar)

        self._construir_ui()
        self._cargar_anio_si_existe(self.campo_anio.value())
        self._actualizar_snapshot()

    # --- UI ---------------------------------------------------------------------------

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        guia = QLabel(
            "Pídele a tu contador la UVT del año, las bases mínimas y las tarifas. "
            "Luego carga el archivo que te dé o escribe los datos aquí y pulsa Guardar datos."
        )
        guia.setWordWrap(True)
        layout.addWidget(guia)

        formulario = QWidget()
        grilla = QGridLayout(formulario)
        grilla.addWidget(QLabel("Año"), 0, 0)
        grilla.addWidget(self.campo_anio, 0, 1)
        grilla.addWidget(QLabel("UVT en pesos"), 1, 0)
        grilla.addWidget(self.campo_uvt, 1, 1)
        grilla.addWidget(QLabel("Fuente / validado por (opcional)"), 2, 0)
        grilla.addWidget(self.campo_fuente, 2, 1)
        grilla.addWidget(QLabel("Fecha de validación (opcional)"), 3, 0)
        grilla.addWidget(self.campo_fecha, 3, 1)
        grilla.setColumnStretch(1, 1)
        layout.addWidget(formulario)

        ayuda_base = QLabel(
            "Base mínima 0 = sin mínimo. Un campo vacío sigue siendo «dato faltante»."
        )
        ayuda_base.setWordWrap(True)
        layout.addWidget(ayuda_base)

        # Columnas estiradas al ancho de la ventana.
        from PySide6.QtWidgets import QHeaderView

        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

        acciones = QWidget()
        fila = QGridLayout(acciones)
        fila.addWidget(self.btn_cargar, 0, 0)
        fila.addWidget(self.btn_agregar, 0, 1)
        fila.addWidget(self.btn_quitar, 0, 2)
        fila.addWidget(self.btn_guardar, 0, 3)
        fila.addWidget(self.btn_cerrar, 0, 4)
        fila.setColumnStretch(5, 1)
        layout.addWidget(acciones)

        layout.addWidget(self._estado)
        self.resize(720, 520)

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
            fuente=self.campo_fuente.text().strip(),
            fecha_validacion=self.campo_fecha.text().strip(),
        )
        self._limpiar_marcas()
        self._estado.setText(f"Datos guardados para el año {self.campo_anio.value()}. Ya puedes cerrar.")
        self._actualizar_snapshot()
        return ruta

    def _conceptos_del_formulario(self) -> dict[str, dict[str, str]]:
        conceptos: dict[str, dict[str, str]] = {}
        for fila in range(self.tabla.rowCount()):
            concepto = self._texto_celda(fila, 0).strip().lower()
            if not concepto:
                continue
            tarifa_decimal = _tarifa_decimal(self._texto_celda(fila, 2))
            conceptos[concepto] = {
                "base_minima_uvt": self._texto_celda(fila, 1),
                "tarifa": _texto_decimal(tarifa_decimal) if tarifa_decimal is not None else self._texto_celda(fila, 2),
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
        if nombre:
            existentes = {self._texto_celda(f, 0).strip().lower() for f in range(self.tabla.rowCount())}
            if nombre.strip().lower() in existentes:
                self._estado.setText(f"El concepto «{nombre}» ya existe; no se permiten duplicados.")
                return
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        self.tabla.setItem(fila, 0, QTableWidgetItem(nombre))
        self.tabla.setItem(fila, 1, QTableWidgetItem(""))
        self.tabla.setItem(fila, 2, QTableWidgetItem(""))

    def _on_agregar_concepto(self) -> None:
        self.agregar_concepto()

    def quitar_concepto(self, fila: int | None = None) -> None:
        if self.tabla.rowCount() <= 0:
            return
        indice = fila if fila is not None else self.tabla.currentRow()
        if indice < 0:
            indice = self.tabla.rowCount() - 1
        self.tabla.removeRow(indice)

    def _on_quitar_concepto(self) -> None:
        if self.tabla.rowCount() <= len(CONCEPTOS):
            self._estado.setText("No puedes quitar los conceptos base del año.")
            return
        self.quitar_concepto()

    def _texto_celda(self, fila: int, columna: int) -> str:
        item = self.tabla.item(fila, columna)
        return item.text().strip() if item is not None else ""

    def _mostrar(self, configuracion: ConfiguracionTributaria) -> None:
        self.campo_anio.blockSignals(True)
        self.campo_anio.setValue(configuracion.anio)
        self.campo_anio.blockSignals(False)
        self.campo_uvt.setText(_texto_decimal(configuracion.uvt_pesos))
        self.campo_fuente.setText(getattr(configuracion, "fuente", "") or "")
        self.campo_fecha.setText(getattr(configuracion, "fecha_validacion", "") or "")
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
            # La tarifa se muestra en % (0.05 -> 5).
            if dato:
                porcentaje = dato.tarifa * Decimal("100")
                self.tabla.setItem(fila, 2, QTableWidgetItem(_texto_decimal(porcentaje)))
            else:
                self.tabla.setItem(fila, 2, QTableWidgetItem(""))
        self._limpiar_marcas()
        self._actualizar_snapshot()

    def _limpiar(self) -> None:
        self.campo_uvt.clear()
        self.campo_fuente.clear()
        self.campo_fecha.clear()
        for fila in range(self.tabla.rowCount()):
            self.tabla.setItem(fila, 1, QTableWidgetItem(""))
            self.tabla.setItem(fila, 2, QTableWidgetItem(""))
        self._limpiar_marcas()

    # --- Acciones ---------------------------------------------------------------------

    def _cargar_anio_si_existe(self, anio: int) -> None:
        self._limpiando = True
        ruta = self.directorio_reglas / f"{anio}.yaml"
        if not ruta.is_file():
            self._limpiar()
            self._estado.setText(
                f"Todavía no hay datos guardados para el año {anio}. "
                "Completa los datos que te dio tu contador y pulsa «Guardar datos»."
            )
            self._limpiando = False
            self._actualizar_snapshot()
            return
        try:
            configuracion = cargar_desde_archivo(ruta, anio)
        except ErrorConfiguracion as exc:
            self._limpiar()
            self._estado.setText(f"No se pudieron leer los datos guardados del año {anio}: {exc}")
            self._limpiando = False
            self._actualizar_snapshot()
            return
        self._mostrar(configuracion)
        self._estado.setText(f"Datos del año {anio} ya guardados. Revísalos si quieres cambiarlos.")
        self._limpiando = False

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
        self._limpiar_marcas()
        try:
            self.guardar()
        except ErrorConfiguracion as exc:
            marcadas = self._marcar_errores()
            if marcadas:
                self._estado.setText(f"No se guardó: {exc} Revísalas: {', '.join(marcadas)}.")
            else:
                self._estado.setText(f"No se guardó: {exc}")

    # --- Validación visual y cierre ----------------------------------------------------

    def _snapshot(self) -> str:
        filas = []
        for f in range(self.tabla.rowCount()):
            filas.append(f"{self._texto_celda(f, 0)}|{self._texto_celda(f, 1)}|{self._texto_celda(f, 2)}")
        return f"{self.campo_uvt.text()}|{self.campo_fuente.text()}|{self.campo_fecha.text()}||" + ";".join(filas)

    def _actualizar_snapshot(self) -> None:
        self._snapshot_guardado = self._snapshot()

    def _hay_cambios_sin_guardar(self) -> bool:
        return self._snapshot() != self._snapshot_guardado

    def _on_cerrar(self) -> None:
        if self._hay_cambios_sin_guardar():
            respuesta = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Quieres cerrar sin guardar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return
        self.close()

    def closeEvent(self, evento) -> None:
        if self._hay_cambios_sin_guardar():
            respuesta = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Quieres cerrar sin guardar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                evento.ignore()
                return
        super().closeEvent(evento)

    def _limpiar_marcas(self) -> None:
        for f in range(self.tabla.rowCount()):
            for c in range(self.tabla.columnCount()):
                item = self.tabla.item(f, c)
                if item is not None:
                    item.setBackground(QBrush(Qt.white))

    def _marcar(self, fila: int, columna: int, etiqueta: str, marcadas: list[str]) -> None:
        item = self.tabla.item(fila, columna)
        if item is None:
            item = QTableWidgetItem("")
            self.tabla.setItem(fila, columna, item)
        item.setBackground(QBrush(QColor("#f4cccc")))
        if etiqueta not in marcadas:
            marcadas.append(etiqueta)

    def _marcar_errores(self) -> list[str]:
        marcadas: list[str] = []
        from decimal import Decimal as _Dec

        uvt = self.campo_uvt.text().strip()
        if not uvt:
            self.campo_uvt.setStyleSheet("background:#f4cccc;")
            marcadas.append("UVT")
        else:
            try:
                _Dec(uvt)
                if _Dec(uvt) <= 0:
                    self.campo_uvt.setStyleSheet("background:#f4cccc;")
                    marcadas.append("UVT")
                else:
                    self.campo_uvt.setStyleSheet("")
            except Exception:
                self.campo_uvt.setStyleSheet("background:#f4cccc;")
                marcadas.append("UVT")
        vistos: dict[str, int] = {}
        for fila in range(self.tabla.rowCount()):
            concepto = self._texto_celda(fila, 0)
            base = self._texto_celda(fila, 1)
            tarifa = self._texto_celda(fila, 2)
            clave = concepto.strip().lower()
            if clave and clave in vistos:
                self._marcar(fila, 0, f"Concepto duplicado: {concepto}", marcadas)
            elif clave:
                vistos[clave] = fila
            if not concepto:
                self._marcar(fila, 0, f"Fila {fila + 1} sin nombre", marcadas)
            if not base:
                self._marcar(fila, 1, f"{concepto or 'Fila'} base mínima", marcadas)
            elif not _es_numero_valido(base):
                self._marcar(fila, 1, f"{concepto} base mínima", marcadas)
            if not tarifa:
                self._marcar(fila, 2, f"{concepto or 'Fila'} tarifa", marcadas)
            elif _tarifa_decimal(tarifa) is None:
                self._marcar(fila, 2, f"{concepto} tarifa", marcadas)
        return marcadas


def _es_numero_valido(texto: str) -> bool:
    try:
        Decimal(texto.replace(",", "."))
        return True
    except Exception:
        return False


def _tarifa_decimal(texto: str) -> Decimal | None:
    """Convierte «4», «4%» o «2,5» (UI, %) a decimal para el YAML. None si no vale."""
    limpio = texto.strip().replace("%", "").strip().replace(",", ".")
    if not limpio:
        return None
    try:
        porcentaje = Decimal(limpio)
    except Exception:
        return None
    if porcentaje < 0 or porcentaje > 100:
        return None
    return porcentaje / Decimal("100")


def _texto_decimal(valor: Decimal) -> str:
    """Sin notación científica ni ceros de más: 220000 y 0.05 se muestran tal cual."""
    texto = format(valor, "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto
