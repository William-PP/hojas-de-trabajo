# Estructura medida de las hojas de referencia

Levantado leyendo directamente las tres hojas de `Referencias/` con openpyxl (sin abrirlas en Excel).
Los archivos no se versionan; aquí solo se documenta su **forma**, no sus datos.

| Alias | Archivo | Documentos en `Dian` | Pestañas |
|---|---|---|---|
| R-A | `1-...Oct.2026.xlsm` | 52 | Dian, Sumatorias, Ventas, Compras |
| R-B | `2-...Sep.2026.xlsm` | 53 | Dian, Sumatorias, Ventas, Compras |
| R-C | `3-...Oct.2026.xlsm` | 89 | Dian, Sumatorias, Ventas, Compras |

Ninguna tiene `Retefuente [Mes]`.

---

## 1. Hoja `Dian`

- 32 columnas (A..AF), encabezado en la fila 1 con relleno `#348441` y texto blanco.
- Datos desde la fila 2, una fila por documento.
- `freeze_panes = A2`, autofiltro `A1:AF{n}` **correcto** en las tres.
- `max_row` = 1000 en las tres: formato aplicado a filas vacías. Al generar no se replican.
- Nómina trae `Divisa`, `Forma de Pago` y `Medio de Pago` como **cadena vacía** (`''`), no `None`.
- Tipos de documento observados: `Factura electrónica`, `Nota de crédito electrónica`,
  `Documento soporte con no obligados`, `Documento equivalente - Servicios públicos domiciliarios`,
  `Nomina Individual` y `Application response`.

## 2. Hojas de trabajo (`Sumatorias`, `Ventas`, `Compras`)

Mismo esqueleto en las tres:

```
fila 1   combinada E1:S1  nombre del cliente
fila 2   combinada E2:S2  NIT.
fila 3   combinada E3:S3  LISTADO DOCUMENTOS ELECTRONICOS DIAN {MES} {AÑO}
fila 4   encabezados C..T (18 columnas)
```

Encabezados de la fila 4:

`Tipo de documento | CUFE/CUDE | Folio | Prefijo | Divisa | Forma de Pago | Medio de Pago |
Fecha Emisión | Fecha Recepción | NIT Emisor | Nombre Emisor | NIT Receptor | Nombre Receptor |
IVA | Total Neto | Total | Estado | Grupo`

- `freeze_panes = A5` en las tres.
- `Total Neto` es fórmula `=R{fila}-P{fila}` en cada fila de datos.
- Cada fila de datos tiene en A y B valores **booleanos** (DIAN / FISICA).

### Distribución de filas

`Sumatorias` arranca los bloques en la fila 7 (fila 5 = título general, fila 6 en blanco).
`Ventas` y `Compras` arrancan en la fila 5 (el título del bloque es la fila 5).

Patrón de cada bloque: **fila de título → filas de datos → fila de total**, y luego **dos filas
en blanco** antes del siguiente bloque. En R-C:

| Hoja | Bloque | Título | Datos | Total |
|---|---|---|---|---|
| Sumatorias | Facturas de ventas | 7 | 8 | 9 |
| Sumatorias | Facturas de compras | 12 | 13–96 | 97 |
| Sumatorias | Devoluciones en compras | 100 | 101–103 | 104 |
| Sumatorias | Nómina | 107 | 108 | 109 |

En la fila de total, la etiqueta va en **O** y los totales en **P** (IVA), **Q** (Total Neto) y
**R** (Total). O es la columna `Nombre Receptor`: la etiqueta se superpone a propósito.

### Verificación de cuadre en R-C

- Filas de datos en `Dian`: 89. Filas con CUFE en `Sumatorias`: 89.
- Suma de los cuatro totales de bloque (R): **36.190.379,92**.
- Suma de la columna `Total` de `Dian`: **36.190.379,92**.
- Totales por columna: IVA 5.113.527,62 · Total Neto 31.076.852,30 · Total 36.190.379,92.

Confirmado: las notas crédito suman **en positivo** y el cuadre es suma directa de bloques.

---

## 3. Anomalías encontradas en las referencias

Se documentan porque son justo los casos que el código tiene que resolver, y porque el golden
tiene que tolerarlas.

| Anomalía | Dónde | Tratamiento propuesto |
|---|---|---|
| `Application response` (52 en `Dian`, 51 en `Sumatorias`) | R-A | categoría propia, excluida y reportada (D-08) |
| Combinación `D1:V1` en vez de `E1:S1` | R-B | normalizar a `E1:S1` (D-15) |
| Fila 2 sin el prefijo `NIT.` | R-B | normalizar (D-15) |
| `TOTAL FACTURA VENTAS`, `TOTAL FACTURAS COMPRAS` | R-B | literales canónicos (D-04) |
| `DEVOLUCIONES EN VENTA` (singular) | R-A | `DEVOLUCIONES EN VENTAS` (D-04) |
| `NOMINA  ` y `TOTAL NOMINA ` con espacios finales | las tres | `strip()` (D-04) |
| Autofiltro termina antes del último dato | R-A, R-C | recalcular (D-13) |
| Totales con `=P8`, `=SUM(...)` y `=P101+P102+P103` | las tres | siempre `SUM` (D-06) |
| Fila de total de devoluciones sin suma cuando hay un solo documento | R-B | `SUM` uniforme |
| `Compras` con la nómina al final, después de devoluciones | las tres | mismo orden en todas las hojas |

---

## 4. Estilos

| Elemento | Valor |
|---|---|
| Fuente | Calibri |
| Encabezado fila 4 | negrita, 10 pt, blanco, relleno `#348441`, centrado |
| Título general (`Sumatorias` fila 5) | negrita, 13 pt, relleno `#DBE5F1` |
| Títulos de bloque | negrita, 11 pt, relleno `#DBE5F1` |
| Formato monetario P/Q/R | `"$"\ #,##0;[Red]\-"$"\ #,##0` |
| Anchos C..T | `8.7, 13, 13, 13, 13, 13, 13, 13, 13, 13, 35.6, 8.7, 35.6, 12.1, 13.9, 12.7, 8.7, 13` |
