# Plan de la Fase 4 — Perfiles, configuración editable, soportes opcionales y `.exe`

Objetivo: cerrar el alcance opcional de `AGENTS.md` §9 con dos ajustes pedidos por el usuario:

1. **El OCR nunca es obligatorio**: la aplicación funciona completa sin PDF ni imágenes.
2. **La configuración tributaria se puede editar desde la interfaz**, para que alguien sin
   conocimientos técnicos cambie UVT, bases mínimas y tarifas; y también se puede **cargar** un
   YAML existente.

Estado: **implementada** (cierre abajo).

---

## 1. Decisiones de diseño (D-37…D-43 registradas en `DECISIONES.md`)

| # | Decisión |
|---|---|
| D-37 | Perfiles por cliente en SQLite (nombre, NIT, carpeta de salida) |
| D-38 | Editor gráfico de `reglas/[año].yaml` con validación, sin valores por defecto |
| D-39 | «Cargar YAML»: se valida, se muestra y solo al guardar se copia a `reglas/[año].yaml` |
| D-40 | OCR opcional con extra `[ocr]`; la app avisa si falta y sigue |
| D-41 | Cruce de soportes por CUFE o prefijo+folio; solo marca `FISICA = TRUE`, no bloquea |
| D-42 | Resolución de carpetas con variables de entorno y soporte para PyInstaller |
| D-43 | Empaquetado `onedir` con PyInstaller y `reglas/` externa al ejecutable |

---

## 2. Módulos implementados en esta fase

| Módulo | Contenido |
|---|---|
| `reglas/configuracion.py` | `construir_configuracion`, `guardar_configuracion`, `texto_configuracion`, `cargar_desde_archivo` (además de lo de Fase 3). |
| `dominio/modelos.py` | `PerfilCliente` (cliente + carpeta de salida). |
| `dominio/soportes.py` | `normalizar_texto`, `documentos_en_texto` (lógica pura del cruce). |
| `infraestructura/repo_sqlite.py` | Tabla `perfiles_cliente` y métodos `guardar_perfil`, `perfiles`, `perfil`, `eliminar_perfil`. |
| `infraestructura/ocr.py` | Adaptador `Ocr` opcional, `ErrorOcr`, `ocr_disponible`; motor inyectable para pruebas. |
| `puertos.py` | Protocolo `OcrProveedor`; `EscritorHoja` acepta `soportes_verificados`. |
| `rutas.py` | `directorio_reglas`, `directorio_datos` (repositorio, entorno y `.exe`). |
| `interfaz/vistas/configuracion.py` | Diálogo para editar y guardar el YAML, y cargar uno existente. |
| `interfaz/vistas/main_window.py` | Combo de perfiles, botón «Guardar cliente», botón de configuración y verificación de soportes. |
| `infraestructura/escritor_xlsx.py` | Marca `FISICA = TRUE` para los CUFEs con soporte verificado. |
| `__main__.py`, `dian_hojas.spec`, `scripts/construir_exe.ps1` | Entrada ejecutable y empaquetado. |

---

## 3. Pruebas

| Archivo | Qué cubre |
|---|---|
| `tests/test_configuracion_editor.py` | Ida y vuelta YAML, textos de la interfaz, UVT/tarifas inválidas, conceptos faltantes, año del archivo. |
| `tests/test_perfiles.py` | Guardar, actualizar, conservar ceros a la izquierda y eliminar perfiles. |
| `tests/test_soportes.py` | Normalización, CUFE con espacios, folio alfanumérico, prefijo+folio, falsos positivos. |
| `tests/test_ocr.py` | Motor inyectado, texto vacío, archivo inexistente y errores del motor. |
| `tests/test_rutas.py` | Variables de entorno y rutas por defecto. |
| `tests/test_escritor.py` | `FISICA = TRUE` solo para el CUFE verificado. |
| `tests/test_interfaz.py` | Diálogo de configuración (carga/guarda y validación), perfiles y OCR opcional. |

---

## 4. Cierre de la Fase 4

### Criterios de aceptación — estado

| Criterio | Estado |
|---|---|
| Perfiles por cliente | ✅ guardados en SQLite y recuperables desde la ventana |
| Editar UVT, bases y tarifas sin tocar YAML | ✅ diálogo con validación y mensajes claros |
| Cargar un YAML existente | ✅ «Cargar YAML existente…» |
| OCR opcional | ✅ botón separado; sin OCR la app funciona igual |
| Cruce con soportes físicos | ✅ marca `FISICA` por CUFE/prefijo+folio |
| Empaquetado `.exe` | ✅ `dian_hojas.spec` + script de construcción |
| Reglas fuera del binario | ✅ `reglas/` al lado del `.exe` o vía `DIAN_HOJAS_REGLAS` |

### Pendiente

- Probar el `.exe` en una máquina limpia (sin Python instalado).
- El YAML real de 2026 (D-18) sigue pendiente de que lo entregue el usuario; el editor ya está
  listo para recibirlo.

---

## 5. Próximo paso

Fase 4 cerrada. Cualquier trabajo adicional (perfiles con reglas propias por cliente, OCR masivo,
empaquetado con instalador) queda para una fase 5 solo si el usuario lo pide.
