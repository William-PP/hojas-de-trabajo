"""ViewModels de la interfaz: orquestan los casos de uso sin acoplarse a Qt de más."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from dian_hojas.aplicacion.procesar_mes import ResultadoProcesamiento, procesar_mes
from dian_hojas.dominio.modelos import Cliente, Periodo
from dian_hojas.infraestructura.lector_dian_xlsx import LectorDianXlsx


class HiloProcesar(QObject):
    """Ejecuta `procesar_mes` en un hilo de trabajo sin bloquear la interfaz.

    Se mueve a un `QThread` desde la ventana principal antes de conectarse; aquí solo es el
    trabajador con sus señales. Las señales se conectan a slots de la UI (hilo de la GUI), así que
    el resultado llega por conexión en cola.
    """

    termino = Signal(object)
    error = Signal(str)
    finished = Signal()
    # Las mismas señales, con un número de generación para descartar resultados viejos:
    # si el usuario reprocesa, lo que llegue tarde del intento anterior no debe pisar la vista.
    termino_generacion = Signal(object, int)
    error_generacion = Signal(str, int)

    def __init__(
        self,
        ruta: Path,
        cliente: Cliente,
        periodo: Periodo,
        generacion: int = 0,
    ) -> None:
        super().__init__()
        self._ruta = Path(ruta)
        self._cliente = cliente
        self._periodo = periodo
        self.generacion = generacion

    @Slot()
    def trabajar(self) -> None:
        try:
            self._resultado = procesar_mes(self._ruta, self._cliente, self._periodo, LectorDianXlsx())
        except Exception as exc:  # pragma: no cover - el hilo no depura excepciones Qt
            mensaje = f"No se pudo procesar el listado: {exc}"
            self.error.emit(mensaje)
            self.error_generacion.emit(mensaje, self.generacion)
            self.termino.emit(None)
            self.termino_generacion.emit(None, self.generacion)
        else:
            self.termino.emit(self._resultado)
            self.termino_generacion.emit(self._resultado, self.generacion)
        finally:
            self.finished.emit()
