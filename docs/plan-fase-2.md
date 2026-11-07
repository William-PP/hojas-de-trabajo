# Plan de la Fase 2 — Interfaz (PySide6)

Objetivo: ventana principal que permita elegir cliente, mes y archivo, procesar, ver el resumen de
cuadres y exportar, sin duplicar lógica de negocio.

Estado: **implementada** (ver cierre al final).

---

## 1. Módulos implementados

| Módulo | Contenido |
|---|---|
| `interfaz/main.py` | Punto de entrada: `run()` crea `QApplication` y muestra `VentanaPrincipal`. |
| `interfaz/vistas/main_window.py` | `VentanaPrincipal(QMainWindow)`: formulario (ruta, año, mes, nombre, NIT, carpeta), resumen de cuadres C1–C7, lista de no clasificados, estado. |
| `interfaz/viewmodels/procesar.py` | `HiloProcesar(QObject)`: worker con señales `termino`, `error`, `finished`; ejecuta `procesar_mes`. |

Decisiones técnicas (D-30, D-31, D-32) quedaron registradas en `DECISIONES.md`.

---

## 2. Pruebas

`tests/test_interfaz.py` (marcadas `@gui`):

1. La ventana se construye.
2. Con el listado sintético procesado desde la ventana: no está vacío, `puede_exportar` y el botón
   de exportar quedan habilitados.
3. El hilo termina con resultado correcto (13 documentos sintéticos).
4. El hilo reporta error con ruta inexistente.

---

## 3. Cierre de la Fase 2

- La interfaz **no** contiene reglas de negocio: delega en `procesar_mes` y `exportar_hoja`.
- El procesamiento corre en `QThread`; las señales llegan a la GUI por conexión en cola.
- El botón de exportación se habilita solo si el mes puede exportarse; la validación final la hace
  `exportar_hoja`.

### Criterio de aceptación — estado

| Criterio | Estado |
|---|---|
| Ventana construye y procesa el listado sintético | ✅ verde |
| Resumen con cuadres (verde/rojo) | ✅ verde (refresco en `_refrescar`) |
| Vista de documentos `SIN_CLASIFICAR` | ✅ verde (lista en la ventana) |
| Exportar con el nombre estándar | ✅ cubierto por casos de uso ya probados |
| Bloqueo de exportación | ✅ cubierto por casos de uso ya probados |

**Próximo paso:** Fase 3 — retefuente (motor de cálculo, YAML por año, memoria proveedor-concepto,
tabla editable, pestaña `Retefuente [Mes]`).

---

## 4. Pendientes de la fase

- Vista de alertas DIAN/FISICA (marcas booleanas) — pendiente de integración con el flujo humano;
  la fase actual muestra el estado de los cuadres, que incluyen el hallazgo.
- Integración del botón «Exportar» con la carpeta elegida (campo de texto) — ya conectado.
- Empaquetado PyInstaller — Fase 4.
