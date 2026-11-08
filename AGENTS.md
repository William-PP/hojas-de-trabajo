# AGENTS.md — Automatización de hojas de trabajo DIAN y retención en la fuente

> Este archivo es el contexto permanente del proyecto. Léelo completo antes de escribir código.
> Trabaja **por fases**, no avances a la siguiente sin que yo lo apruebe.
> Idioma del código: nombres de dominio en español (como en este documento); comentarios y mensajes de usuario en español.

---

## 1. Qué es el proyecto

Una aplicación de escritorio en Python, con interfaz gráfica, que automatiza la preparación mensual de **hojas de trabajo de retención en la fuente** para clientes (personas naturales o empresas) en Colombia.

**Entrada:** el listado de documentos electrónicos que se descarga manualmente de la DIAN (Excel).
**Salida:** un archivo Excel con las pestañas:

`Dian` | `Sumatorias` | `Ventas` | `Compras` | `Retefuente [Mes]`

Hoy este trabajo se hace a mano. La app debe replicarlo con exactitud y añadir cuadres automáticos.

---

## 2. Flujo manual actual (lo que se automatiza y lo que no)

1. Ingresar a `https://www.dian.gov.co/` → "Facturando Electrónicamente".
2. Autenticarse (empresa: representante legal + NIT; persona: cédula) y abrir el link que llega al correo (dura ~1 hora).
3. *Histórico* → *Descarga de listados* → mes y año, **día 1 al 31** → *Exportar Excel* → descargar.
4. Subir a Drive: `Cliente / Asuntos Tributarios / Hojas de Trabajo / Mensual / [Año]`.
5. Construir las pestañas duplicando y depurando (sección 4).

### Dentro del alcance
- Importar y validar el Excel de la DIAN.
- Clasificar documentos.
- Generar las pestañas `Dian`, `Sumatorias`, `Ventas`, `Compras`.
- Cuadres automáticos.
- Pestaña `Retefuente` asistida (la app sugiere, el usuario confirma).
- Guardar el archivo con el nombre estándar.

### Fuera del alcance (no lo implementes)
- **Login y descarga automática desde la DIAN** (link por correo con vencimiento, posibles captchas, portal cambiante).
- Subida por API a Google Drive (se usa la carpeta sincronizada de Drive para escritorio).
- Presentación del formulario de retención y contabilización.
- OCR de facturas físicas (posible fase futura).
- **Decidir criterio tributario final**: la app sugiere y calcula; el usuario confirma.

---

## 3. Entrada: el archivo de la DIAN

Una tabla de **32 columnas** (A a AF), fila 1 de encabezados. En el ejemplo de referencia es una tabla de Excel (`ref A1:AF90`).

| Col | Campo | Notas |
|---|---|---|
| A | Tipo de documento | Ver sección 3.1 |
| B | CUFE/CUDE | Identificador único: úsalo para detectar duplicados |
| C | Folio | **Texto** (puede traer letras, p. ej. `NCP14858`) |
| D | Prefijo | Puede venir vacío |
| E | Divisa | |
| F | Forma de Pago | |
| G | Medio de Pago | |
| H | Fecha Emisión | **Texto** con formato `dd-mm-aaaa` |
| I | Fecha Recepción | **Texto** ISO `aaaa-mm-ddThh:mm:ss` |
| J / K | NIT / Nombre Emisor | |
| L / M | NIT / Nombre Receptor | |
| N | IVA | |
| O–Z | ICA, IC, INC, Timbre, INC Bolsas, IN Carbono, IN Combustibles, IC Datos, ICL, INPP, IBUA, ICUI | Normalmente 0 |
| AA / AB / AC | Rete IVA / Rete Renta / Rete ICA | Retenciones informadas |
| AD | Total | |
| AE | Estado | "Aprobado" o "Aprobado con notificación" |
| AF | **Grupo** | **Emitido** o **Recibido** |

NITs y folios deben tratarse como **texto**, nunca como número.

### 3.1 Tipos de documento y su categoría

Se observaron estos tipos. **El Grupo (Emitido/Recibido) se evalúa junto con el tipo.**

| Tipo de documento | Grupo | Categoría |
|---|---|---|
| Factura electrónica | Emitido | `VENTA` |
| Factura electrónica | Recibido | `COMPRA` |
| Documento soporte con no obligados | Emitido | `COMPRA` (es una compra del cliente a un no obligado a facturar) |
| Documento equivalente (p. ej. servicios públicos domiciliarios) | Recibido | `COMPRA` |
| Nota de crédito electrónica | Recibido | `DEVOLUCION_COMPRA` |
| Nota de crédito electrónica | Emitido | `DEVOLUCION_VENTA` |
| Nomina Individual | Emitido | `NOMINA` |

**Trampa conocida:** "Emitido" no significa venta. El documento soporte y la nómina son "Emitidos" pero son costos del cliente.

Cualquier combinación no listada va a `SIN_CLASIFICAR` y se muestra al usuario. **Nunca descartar un documento en silencio.**

---

## 4. Salida: estructura exacta del Excel

Replica la hoja de referencia (`fixtures/hoja_referencia_oct_2026.xlsx`). Usa esa hoja como fuente de verdad en caso de duda.

### 4.1 `Dian`
- Copia **exacta** del archivo original. **No modificar nada** (ni valores, ni orden, ni formato).

### 4.2 `Sumatorias`
- Tabla en columnas **C a T**; columnas A y B reservadas para márgenes.
- Filas 1–3 con celdas combinadas `E1:S1`, `E2:S2`, `E3:S3`:
  - Fila 1: nombre del cliente.
  - Fila 2: `NIT. 900.000.001-1` (formato con puntos).
  - Fila 3: `LISTADO DOCUMENTOS ELECTRONICOS DIAN [MES EN MAYÚSCULAS] [AÑO]`.
- Fila 4, encabezados (C a T):
  `Tipo de documento | CUFE/CUDE | Folio | Prefijo | Divisa | Forma de Pago | Medio de Pago | Fecha Emisión | Fecha Recepción | NIT Emisor | Nombre Emisor | NIT Receptor | Nombre Receptor | IVA | Total Neto | Total | Estado | Grupo`
- Se conservan solo `IVA` y `Total` de las columnas de impuestos; se agrega `Total Neto`.
- **`Total Neto` es fórmula:** `=R{fila}-P{fila}` (Total − IVA).
- Paneles inmovilizados en `A5`; autofiltro sobre `C4:T{última}`.
- Fila 5: título `REVISION DEL TOTAL DE DOCUMENTOS Y SUMATORIAS` (en C).
- Bloques, cada uno con fila de título (en C) y fila de total (etiqueta en O, totales en P, Q, R):

| Orden | Título del bloque | Etiqueta del total |
|---|---|---|
| 1 | `FACTURAS DE VENTAS` | `TOTAL FACTURAS VENTAS` |
| 2 | `FACTURAS DE COMPRAS` | `TOTAL FACTURAS DE COMPRAS` |
| 3 | `DEVOLUCIONES EN COMPRAS` | `TOTAL DEVOLUCIONES EN COMPRAS` |
| 4 | `NOMINA` | `TOTAL NOMINA` |
| (si hay) | `DEVOLUCIONES EN VENTAS` | `TOTAL DEVOLUCIONES EN VENTAS` |

- Fórmulas de total (usa `SUM` con rango para cualquier bloque con más de una fila):
  - Un documento: `=P8`
  - Varios: `=SUM(P13:P96)` (igual para Q y R)
  - En el ejemplo de referencia las devoluciones usan `=P101+P102+P103`; **en el código usa `SUM(rango)`**, que no se rompe al agregar filas.

### 4.3 `Ventas`
- Misma estructura de encabezado (filas 1–4), freeze `A5` y autofiltro.
- Solo el bloque `FACTURAS DE VENTAS` (y `DEVOLUCIONES EN VENTAS` si existen) con sus totales.
- Fila del título (fila 5) incluye en **A5 = `DIAN`** y **B5 = `FISICA`**; cada fila de documento tiene en A y B **casillas booleanas** (celdas con `TRUE`/`FALSE`):
  - A (DIAN): el documento está en el listado de la DIAN.
  - B (FISICA): el documento fue verificado contra el soporte que entregó el cliente.
  - Una sola marca = **alerta** para revisar.

### 4.4 `Compras`
- Igual a `Ventas` pero con los bloques `FACTURAS DE COMPRAS`, `DEVOLUCIONES EN COMPRAS` y `NOMINA`.
- Incluye documento soporte y documentos equivalentes dentro de `FACTURAS DE COMPRAS`.
- Orden de las facturas: **fecha de emisión descendente** (más reciente primero). Usar siempre el mismo criterio.
- Columnas A y B como en `Ventas`.
- **Cuadre:** `Ventas + Compras (+ devoluciones y nómina) = Sumatorias`.

### 4.5 `Retefuente [Mes]` (p. ej. `Retefuente Octubre`)
- Parte de una copia de `Compras`.
- Columnas de trabajo agregadas a la derecha:

| Columna | Contenido |
|---|---|
| Concepto de retención | Compras, servicios, honorarios, arrendamientos, transporte… o `No aplica` |
| Base de retención | Normalmente `Total Neto` |
| Base mínima (UVT) | Del concepto, según el año |
| ¿Supera la base? | Sí / No |
| Tarifa | Del concepto, según el año |
| Retención | `=SI(supera, base*tarifa, 0)` |
| Observaciones | Régimen del proveedor, autorretenedor, etc. |

- Resumen al final por concepto: base total, tarifa, retención y `TOTAL RETENCIÓN A DECLARAR`.
- Criterios de revisión por factura (en orden): ¿el cliente es agente de retención? → ¿qué se compró? → ¿quién es el proveedor (régimen, autorretenedor, gran contribuyente, declarante)? → ¿supera la base mínima en UVT? → ¿aplica Rete IVA o Rete ICA?
- Casos frecuentes: servicios públicos (normalmente sin retención), notas crédito (restan), nómina (se maneja aparte), proveedores autorretenedores (no se les retiene).

### 4.6 Nombre del archivo

```
[N° mes]-Hoja_de_trabajo_Rtefte_[Mes abrev]_[Año]_[Nombre_Cliente].xlsx
```
Ejemplo: `10-Hoja_de_trabajo_Rtefte_Oct_2026_Nombre_Cliente.xlsx`

La hoja de referencia es `.xlsm` pero **no contiene macros**; generar `.xlsx`.

---

## 5. Cuadres obligatorios

La app debe calcularlos y mostrarlos, y bloquear la exportación (o advertir de forma visible) si fallan:

1. Cantidad de documentos en `Sumatorias` = filas de datos en `Dian`.
2. Suma de `Total` por bloques en `Sumatorias` = suma de la columna `Total` de `Dian`.
3. Ningún CUFE aparece en más de un bloque ni más de una vez.
4. `Ventas + Compras (+ devoluciones y nómina) = Sumatorias`.
5. Todas las fechas de emisión pertenecen al mes/año seleccionado.
6. El NIT del cliente aparece como emisor o receptor en los documentos.
7. Fórmulas sin errores (`#REF!`, `#VALUE!`, `#NAME?`) tras recalcular.

**Ejemplo de referencia (oct 2026):** 89 documentos = 1 factura emitida (venta) + 84 compras (82 facturas recibidas, 1 documento soporte, 1 documento equivalente) + 3 notas crédito recibidas + 1 nómina. Total de la columna `Total` en `Dian`: 36.190.379,92.

---

## 6. Arquitectura: hexagonal ligera

```
INTERFAZ (PySide6)  →  APLICACIÓN (casos de uso)  →  DOMINIO + REGLAS
                                   │
                              PUERTOS (Protocol)
                                   │
                          ADAPTADORES (xlsx, sqlite, yaml)
```

**Regla de dependencias:** las flechas solo apuntan hacia el centro. El dominio y las reglas **no importan** pandas, openpyxl, PySide6 ni sqlite3.

### 6.1 Capas
- **Dominio (Python puro):** `Cliente`, `Periodo`, `DocumentoElectronico`, `Proveedor`, `LineaRetefuente`, `ResultadoMes`; enums `TipoDocumento`, `Grupo`, `Categoria`; cuadres como funciones puras.
- **Reglas:** `clasificar(documento) → Categoria`; motor de retefuente; tablas por año en YAML.
- **Aplicación (casos de uso):** `ProcesarMes`, `SugerirRetefuente`, `ConfirmarRetefuente`, `ExportarHoja`. Reciben dependencias por parámetro.
- **Puertos (`typing.Protocol`):** `LectorListado`, `EscritorHoja`, `RepositorioProveedores`.
- **Adaptadores:** `LectorDianXlsx`, `EscritorOpenpyxl`, `RepoSqlite`, `ConfigYaml`.
- **Interfaz:** PySide6 con MVVM simple; procesos largos en `QThread`/`QRunnable`.

### 6.2 Estructura de carpetas

```
dian_hojas/
├── AGENTS.md
├── pyproject.toml
├── reglas/
│   ├── 2026.yaml                # UVT, conceptos, bases mínimas, tarifas (los provee el usuario)
│   └── clientes/                # reglas por cliente (opcional)
├── src/dian_hojas/
│   ├── dominio/{modelos.py, enums.py, cuadres.py}
│   ├── reglas/{clasificador.py, retefuente.py}
│   ├── aplicacion/{procesar_mes.py, sugerir_retefuente.py, exportar_hoja.py}
│   ├── puertos.py
│   ├── infraestructura/{lector_dian_xlsx.py, escritor_xlsx.py, repo_sqlite.py, config_yaml.py}
│   └── interfaz/{main.py, vistas/, viewmodels/}
└── tests/
    ├── test_clasificador.py
    ├── test_cuadres.py
    ├── test_integracion_hoja.py
    └── fixtures/                # archivos ANONIMIZADOS
```

---

## 7. Stack tecnológico

| Capa | Herramienta |
|---|---|
| Interfaz | **PySide6** (Qt) |
| Procesamiento de datos | **pandas** |
| Generación de Excel | **openpyxl** (fórmulas vivas, formato, freeze, autofiltro, celdas combinadas) |
| Validación de entrada | **pydantic** |
| Persistencia local | **SQLite** (proveedor → concepto, decisiones, historial) |
| Reglas y configuración | **YAML** (PyYAML) |
| Pruebas | **pytest** (+ `pytest-qt` solo para flujos críticos) |
| Empaquetado | **PyInstaller** |
| Versionado | **git**, un commit por fase |

---

## 8. Reglas no negociables

1. **La pestaña `Dian` no se modifica.** Valores, orden y formato tal como vienen.
2. **Fórmulas vivas en el Excel generado** (`=SUM(...)`, `=R8-P8`), nunca valores calculados en Python. Los cuadres en Python verifican que coincidan.
3. **Nada se descarta en silencio.** Lo no clasificable va a `SIN_CLASIFICAR` y se muestra al usuario.
4. **Las tarifas, UVT y bases mínimas salen únicamente de `reglas/[año].yaml`.** **No inventes ni completes valores tributarios.** Si falta un dato, falla con un mensaje claro pidiéndolo.
5. **La app sugiere, el usuario decide.** Toda sugerencia de concepto de retención queda marcada como `pendiente de confirmar` hasta que el usuario la acepte.
6. **El Excel es una salida, no la base de datos.** Los datos viven en memoria y SQLite; el `.xlsx` se regenera.
7. **Validar al entrar, confiar adentro.** El lector valida columnas, mes y NIT; el resto del código asume datos limpios.
8. **NITs y folios son texto.** No convertir a número ni perder ceros o letras.
9. **Interfaz delgada.** Sin lógica de negocio en las vistas.
10. **Privacidad:** nunca incluir datos reales de clientes en el repositorio, en `fixtures/` ni en logs. Solo archivos anonimizados.
11. **Escribe primero las pruebas** de cada pieza del núcleo.
12. Usa `SUM` con rango en los totales, no sumas celda por celda.

---

## 9. Plan por fases

Trabaja una fase a la vez. Al terminar cada una: ejecuta las pruebas, muestra un resumen de lo hecho y **espera mi aprobación**.

### Fase 0 — Preparación
- Crear el repositorio, `pyproject.toml`, estructura de carpetas, configuración de `pytest`.
- Verificar que existen en `tests/fixtures/` el listado DIAN anonimizado y la hoja de referencia anonimizada.
- Mostrarme el plan antes de escribir código de la fase 1.

### Fase 1 — Núcleo (sin interfaz)
- Dominio, enums, clasificador, cuadres.
- `LectorDianXlsx` con validación (pydantic).
- `EscritorOpenpyxl` que genere `Dian`, `Sumatorias`, `Ventas`, `Compras` como en la sección 4.
- **Criterio de aceptación:** a partir del listado de la DIAN de referencia, el Excel generado coincide con la hoja de referencia en estructura, valores de totales y fórmulas; todos los cuadres de la sección 5 pasan; no hay errores de fórmula tras recalcular.

### Fase 2 — Interfaz
- Ventana principal: elegir cliente, mes y archivo; botón procesar.
- Resumen con conteos, totales y estado de cada cuadre (verde/rojo).
- Vista de documentos `SIN_CLASIFICAR` y alertas DIAN/FISICA.
- Exportar con el nombre estándar.

### Fase 3 — Retefuente
- `reglas/[año].yaml` (lo provee el usuario) y motor de cálculo.
- Memoria proveedor → concepto en SQLite.
- Tabla editable en la interfaz con sugerencias pendientes de confirmar.
- Pestaña `Retefuente [Mes]` y resumen por concepto.

### Fase 4 — Opcional (solo si lo pido)
- Perfiles por cliente, empaquetado `.exe`, cruce automático con soportes físicos, OCR.

---

## 10. Estrategia de pruebas

- **Unitarias:** clasificador (cada combinación tipo/grupo), cuadres, cálculo de retención. Son las más importantes.
- **Integración (golden file):** listado DIAN anonimizado → Excel generado → comparación contra la hoja de referencia ya revisada a mano.
- **Recalculo:** abrir el `.xlsx` generado con LibreOffice, recalcular y verificar que no haya errores de fórmula.
- **Interfaz:** pocas pruebas con `pytest-qt`, solo flujos críticos.

---

## 11. Errores frecuentes a evitar

| Problema | Causa | Solución |
|---|---|---|
| Venta contada como compra (o al revés) | Clasificar solo por tipo | Usar Tipo + Grupo |
| Documento soporte o nómina como venta | Son "Emitidos" pero son costos | Reglas de la sección 3.1 |
| Totales que no cuadran | Duplicados, documentos omitidos, rangos mal calculados | Detectar por CUFE; construir rangos desde los datos |
| Folios o NITs alterados | Lectura como número | Leer como texto (`dtype=str`) |
| Autofiltro desactualizado | Rango fijo | Calcular desde la última fila |
| Fechas mal interpretadas | `dd-mm-aaaa` leído como `mm-dd-aaaa` | Parseo explícito con `dayfirst=True` o formato fijo |

---

## 12. Primera tarea para el agente

> Lee este `AGENTS.md` completo. Ejecuta la **Fase 0** y preséntame un plan detallado de la **Fase 1** (módulos, firmas de funciones, lista de pruebas a escribir y orden de implementación). **No escribas código de la Fase 1 hasta que apruebe el plan.**
