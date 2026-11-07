"""Punto de entrada de la aplicación de interfaz."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from dian_hojas.interfaz.vistas import VentanaPrincipal


def run() -> int:
    """Arranca la aplicación de escritorio."""
    aplicacion = QApplication.instance() or QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    return aplicacion.exec()
