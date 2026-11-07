# Plan de la Fase 3 — Retefuente

Objetivo: pestaña `Retefuente [Mes]` sobre la base de `Compras`, con motor de cálculo, configuración
tributaria por año, memoria proveedor → concepto, sugerencias y resumen.

Estado: **implementada** (cierre abajo).

---

## 1. Decisiones de diseño (D-30…D-35 registradas en `DECISIONES.md`)

| # | Decisión |
|---|---|
| D-30 | Procesamiento en `QThread` desde la ventana |
| D-31 | Botón de exportación solo habilitado si el mes puede exportarse |
| D-32 | Cliente ingresado desde la interfaz por NIT |
| D-33 | Nombre de la pestaña `Retefuente` → `Retefuente Octubre` |
| D-34 | Valores ausentes (`null`) en la configuración tributaria se consideran faltantes |
| D-35 | Pestaña `Retefuente [Mes]` y resumen (`TOTAL RETENCIÓN A DECLARAR`) |

---

## 2. Módulos implementados en esta fase

| Módulo | Contenido |
|---|---|
| `dominio/retefuente.py` | `LineaRetefuente`, `RetefuenteMes`, `retener`, `retefuente_mes` (puro). |
| `reglas/configuracion.py` | `ConfiguracionTributaria`, `ConceptoTributario`, `ErrorConfiguracion`, `cargar_configuracion`. |
| `infraestructura/config_yaml.py` | Puerto `ConfigYaml` → lee `reglas/[año].yaml`. |
| `infraestructura/repo_sqlite.py` | Puerto `RepoSqlite` → proveedor → concepto + decisiones. |
| `puertos.py` | Nuevo puerto `RepositorioProveedores`. |
| `aplicacion/sugerir_retefuente.py` | `sugerir_retefuente`: compras → líneas de retención. |
| `aplicacion/confirmar_retefuente.py` | `confirmar_retefuente`: reaplica decisiones del usuario. |
| `aplicacion/exportar_hoja.py` | Acepta `retefuente` y lo pasa al escritor. |
| `infraestructura/escritor_xlsx.py` | Escribe la pestaña `Retefuente [Mes]` con columnas U..AA y resumen. |
| `infraestructura/plantilla.py` | `nombre_hoja_retefuente`, `COLUMNAS_RETIFUERTE`, columnas U..AA. |
| `infraestructura/estilos.py` | Anchos para columnas U..AA. |

---

## 3. Pruebas

`tests/test_retefuente.py` (8 pruebas): motor (supera/no supera, total), configuración (ok, sin UVT,
conceptos incompletos), sugerencia, confirmación, exportación con retefuente.

---

## 4. Cierre de la Fase 3

- El motor de retención está en el dominio (puro).
- La configuración tributaria llega por YAML; faltantes → error claro (D-34).
- La sugerencia se calcula por proveedor → concepto; el usuario decide (D-32, D-35).
- La pestaña `Retefuente Octubre` se escribe cuando el resultado trae líneas.

### Criterios de aceptación — estado

| Criterio | Estado |
|---|---|
| Tarifas/UVT/bases desde `reglas/[año].yaml` | ✅ con error claro si faltan (D-34) |
| Motor de retención | ✅ verificado con base mínima y supera/no supera |
| Sugerencia → usuario confirma | ✅ `sugerir_retefuente` + `confirmar_retefuente` |
| Pestaña `Retefuente [Mes]` y resumen | ✅ golden de escritura en tests |
| `TOTAL RETENCIÓN A DECLARAR` | ✅ |

### Pendiente

- La tabla **editable** en la interfaz (sugerencias `pendiente de confirmar`) — integración con la
  vista de Fase 2.
- El motor con tarifas reales (D-18) — requiere el YAML que te pido.

---

## 5. Próximo paso

**Fase 4** (opcional): perfiles por cliente, empaquetado `.exe`, cruce automático con soportes físicos, OCR.
