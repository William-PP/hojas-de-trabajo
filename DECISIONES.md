# Decisiones de negocio

Registro de decisiones de **negocio** (qué significa cada cuadre, cada bloque y cada regla
tributaria). Las decisiones de implementación están en `DECISIONES_TECNICAS.md`.

Convención: `R-A` = referencia de 52 documentos (oct), `R-B` = referencia de 53 (sep),
`R-C` = referencia de 89 (oct, la que usa `AGENTS.md` como fuente de verdad).

---
## D-01. Nombre del archivo de salida

`AGENTS.md` §4.6 dice `[Mes abrev]`, la guía dice `[Mes]`; las referencias reales se llaman
`1-Hoja de trabajo Rtefte Oct.2026 .xlsm` (con espacios, punto y espacio final).

**Propuesta:** seguir el ejemplo de `AGENTS.md` al pie de la letra:

```
10-Hoja_de_trabajo_Rtefte_Oct_2026_Nombre_Cliente.xlsx
```

Mes abreviado en español de 3 letras: `Ene, Feb, Mar, Abr, May, Jun, Jul, Ago, Sep, Oct, Nov, Dic`.
Sin espacios, sin punto, sin espacio final. Carpetas destino: las que defina el usuario.

**Estado:** aprobada salvo que prefieras `Octubre` completo.

---

---

## D-04. Nombres canónicos de bloques y etiquetas

Las referencias son inconsistentes entre sí: `TOTAL FACTURA VENTAS` (R-B) vs `TOTAL FACTURAS VENTAS`
(R-C), `TOTAL FACTURAS COMPRAS` (R-B) vs `TOTAL FACTURAS DE COMPRAS` (R-C),
`DEVOLUCIONES EN VENTA` (R-A) vs `DEVOLUCIONES EN VENTAS`, y `NOMINA  ` / `TOTAL NOMINA `
con espacios finales.

**Propuesta:** un solo juego de literales, sin espacios sobrantes:

| Título del bloque | Etiqueta del total |
|---|---|
| `FACTURAS DE VENTAS` | `TOTAL FACTURAS VENTAS` |
| `DEVOLUCIONES EN VENTAS` | `TOTAL DEVOLUCIONES EN VENTAS` |
| `FACTURAS DE COMPRAS` | `TOTAL FACTURAS DE COMPRAS` |
| `DEVOLUCIONES EN COMPRAS` | `TOTAL DEVOLUCIONES EN COMPRAS` |
| `NOMINA` | `TOTAL NOMINA` |
| `REVISION DEL TOTAL DE DOCUMENTOS Y SUMATORIAS` | (título general, fila 5 de `Sumatorias`) |

**Estado:** aprobada (normaliza, no cambia contenido).

---

---

## D-05. Orden de los bloques en `Sumatorias`

`AGENTS.md` lista `DEVOLUCIONES EN VENTAS` al final ("si hay"). `R-A`, que es la única que tiene ese
bloque, lo pone **inmediatamente después de ventas**.

**Propuesta:** `VENTAS` → `DEVOLUCIONES EN VENTAS` (si hay) → `COMPRAS` → `DEVOLUCIONES EN COMPRAS` → `NOMINA`.

**Estado:** aprobada por defecto (propuesta adoptada, la referencia real manda sobre la tabla del `.md`).

---

---

## D-07. Pestaña `Retefuente [Mes]`

Ninguna de las tres referencias tiene esa pestaña: las hojas reales terminan en `Compras`.
No hay golden file para Retefuente.

**Propuesta:** en Fase 3 la pestaña se valida con pruebas unitarias del motor y con una revisión
tuya sobre un caso real; no se compara contra referencia. Y cuando tengamos una hoja con Retefuente
ya trabajada, se agrega como cuarta referencia.

**Estado:** informativa.

---

---

## D-08. Tipo de documento `Application response` ⚠ hallazgo importante

`R-A` trae **un** documento con tipo `Application response` (Grupo `Recibido`, Estado `Aprobado`).
No es una compra ni una venta: es la respuesta de la DIAN a un evento. En `R-A` hay 52 filas en
`Dian` y solo 51 en `Sumatorias`: **el proceso manual lo borró en silencio** (justo lo que la regla 3
prohíbe).

**Propuesta:**

- Nueva categoría `RESPUESTA_DIAN` en el enum `Categoria`, con `incluir_en_hoja = False`.
- No entra en `Sumatorias` ni en las demás pestañas, pero **se lista en el resumen** como documento
  excluido con su motivo, y el usuario puede revisarlo.
- El cuadre 1 pasa a: `filas de Sumatorias + excluidos justificados = filas de Dian`.

**Estado:** aprobada. `RESPUESTA_DIAN` se excluye de las hojas y se lista en el resumen como
documento excluido con su motivo. El cuadre C1 suma los excluidos justificados.

---

---

## D-09. Tipo `Documento equivalente`

El nombre real es `Documento equivalente - Servicios públicos domiciliarios`, no
`Documento equivalente`. Comparar por igualdad exacta lo mandaría a `SIN_CLASIFICAR`.

**Propuesta:** el clasificador compara **normalizado** (sin tildes, minúsculas, espacios colapsados)
y por **prefijo** para `documento equivalente`. Igual criterio para `documento soporte`
(`Documento soporte con no obligados`).

**Estado:** aprobada.

---

---

## D-10. `Documento soporte` con Grupo `Recibido`

`AGENTS.md` solo contempla `Documento soporte` + `Emitido` → `COMPRA`. `R-B` trae uno **recibido**
y el proceso manual lo metió en `Compras`.

**Propuesta:** `Documento soporte` → `COMPRA` con **cualquiera** de los dos grupos.
La columna `Grupo` se conserva y el cuadre 6 (identificación del cliente) se resuelve por
emisor **o** receptor, sin exigir cuál.

**Estado:** aprobada. Ambos grupos van a `COMPRA` y se conserva la columna `Grupo`.

---

---

## D-11. Estado del documento

En las referencias solo aparecen `Aprobado` y `Aprobado con notificación`, y **ambos se incluyen**.

**Propuesta:** incluir los dos. Cualquier otro estado queda en `SIN_CLASIFICAR` con alerta
(no se descarta).

**Estado:** aprobada.

---

---

## D-12. Signo de las notas crédito

Hallazgo: en `R-C` las tres notas crédito tienen `Total` **positivo** (650.001,80 / 58.899,98 / 78.000,00)
y el bloque `DEVOLUCIONES EN COMPRAS` los suma en positivo. La suma de los cuatro bloques da
exactamente 36.190.379,92, igual al total de `Dian`.

**Propuesta:** en `Sumatorias`, `Ventas` y `Compras` **no se invierte el signo**; se copia tal como
viene de la DIAN y el cuadre 2 es la suma directa de bloques. El signo negativo se aplica **solo en
Retefuente**, donde la nota crédito resta de la base del concepto.

**Estado:** aprobada (confirmada contra la referencia).

---

---

## D-15. Encabezado de las filas 1–3

`R-A` y `R-C` combinan `E1:S1`, `E2:S2`, `E3:S3`; `R-B` combina `D1:V1` (error manual) y su fila 2
dice `900.123.456` sin el prefijo `NIT.`.

**Propuesta:** siempre `E1:S1` / `E2:S2` / `E3:S3`, con:

- Fila 1: nombre del cliente.
- Fila 2: `NIT. 900.000.001-1` (con puntos de miles y dígito de verificación si existe);
  para persona natural, `CC. 1.000.000.001`.
- Fila 3: `LISTADO DOCUMENTOS ELECTRONICOS DIAN {MES} {AÑO}` en mayúsculas y sin doble espacio.

**Estado:** aprobada por defecto solo en el prefijo `NIT.` / `CC.`.

---

---

## D-17. Mes sin movimiento

La guía dice "no crees pestañas vacías sin necesidad", pero el estándar de salida son 5 pestañas.

**Propuesta:** si el listado viene sin filas, la app **no exporta**: muestra el aviso
"El listado del mes no tiene documentos" y deja al usuario decidir. Es más honesto que un archivo
vacío que luego se confunde con un mes trabajado.

**Estado:** aprobada. Si el listado no trae filas, no se genera archivo y se avisa.

---

---

## D-18. UVT y bases mínimas en `Retefuente`

La tabla de trabajo solo tiene "Base mínima (UVT)". Para decidir si la factura supera el mínimo hay
que comparar pesos contra pesos, así que falta la UVT del año.

**Propuesta:** el YAML por año trae `uvt_pesos` y, por concepto, `base_minima_uvt` y `tarifa`.
El escritor agrega dos columnas derivadas: `Base mínima (pesos) = uvt * base_minima_uvt` y
`Retención = IF(base >= base_minima_pesos, base * tarifa, 0)`.
Si falta cualquier dato del concepto, la app no genera la pestaña y dice qué clave falta.

**Estado:** ⚠ pendiente (depende de que me pases el YAML de 2026).

---

---

## D-19. Impuestos distintos de IVA

`AGENTS.md` conserva solo `IVA` y `Total`. Si en un mes `ICA`, `INC`, `Timbre` o similares vienen
distintos de cero, `Total Neto = Total − IVA` deja de ser el valor antes de IVA y el cuadre se
degrada sin avisar.

**Propuesta:** validar al leer. Si la suma de impuestos distintos de IVA es ≠ 0, la app **no exporta**
y muestra la lista de documentos afectados. Es preferible a un neto silenciosamente incorrecto.

**Estado:** aprobada. Si la suma es distinta de cero, la app no exporta y lista los documentos
afectados. Cuadre C7.

---

---

## D-23. Las referencias están anonimizadas

En las tres hojas de `Referencias/`, las columnas de NIT y nombres de los documentos vienen como
`x`. La cabecera de `Sumatorias` de la referencia #3 sí conserva el cliente ficticio
(`CLIENTE DE PRUEBA S.A.S.`, `NIT. 900.000.001-1`); las referencias #1 y #2 no traen
cabecera.

**Consecuencia:** el cuadre C6 («el cliente aparece en el listado») **no se puede validar** sobre
estas referencias, porque la identificación real no existe en los datos. La prueba golden:

- lee el cliente de la cabecera cuando está; si no, usa un cliente de prueba,
- comprueba que C6 falla con un detalle claro (es lo correcto: el dato no está),
- valida C1 a C5, que sí son independientes de los NIT.

No se relaja la regla C6 ni se inventan NIT para que pase.

---

---

## D-24. La referencia #3 trae dos facturas con impuestos distintos de IVA

La referencia #3 contiene dos documentos con impuesto distinto de IVA (folios inventados):

| Documento | Impuesto | Valor |
|---|---|---|
| `FV-99901` | INC Bolsas | 219,00 |
| `FV-99902` | INC | 220,53 |

Aplicando D-19, la app **bloquea la exportación** de ese mes y lista ambos documentos. Es el
comportamiento pedido, aunque la hoja de referencia se haya preparado a mano sin corregirlo.

**Decisión para el golden:** la comparación estructural se hace llamando al escritor directamente,
sin pasar por `exportar_hoja` (que aquí bloquea a propósito). La prueba además verifica que:

- C7 falla y menciona exactamente esos dos folios y sus valores,
- `puede_exportar` es `False` y los cuadres fallidos son exactamente `{C6, C7}`.

Así se demuestra que la estructura coincide **y** que la app se niega a exportar en silencio.

---

---

## D-31. El botón de exportación solo se habilita si el mes puede exportarse

`VentanaPrincipal._refrescar` habilita el botón «Exportar hoja de trabajo» solo cuando:

- no hay error del procesamiento,
- `ResultadoProcesamiento.mes_vacio` es `False`,
- `ResultadoProcesamiento.puede_exportar` es `True`.

La exportación en sí la ejecuta `exportar_hoja` (que vuelve a validar). La ventana no replica esas
reglas: solo decide habilitar la acción. Si un cuadre falla, el usuario ve el detalle en la vista de
resumen y el botón queda deshabilitado.

---

---

## D-33. Nombre de la pestaña `Retefuente`

`AGENTS.md` §4.5 la llama `Retefuente [Mes]`, con ejemplo `Retefuente Octubre`.

**Decisión:** el nombre real de la pestaña generada es `Retefuente {Mes en nombre propio}`, por
ejemplo `Retefuente Octubre` para octubre. Se aplica `capitalize()` al nombre completo del mes
(`OCTUBRE` → `Octubre`).

---

---

## D-34. Valores ausentes en la configuración tributaria se consideran faltantes

Un YAML puede traer claves con valor `null`. Para los datos tributarios (UVT, base mínima, tarifa)
un valor `null` se trata como **ausente** y dispara el error de configuración con el concepto
incompleto.

---

---

## D-35. Pestaña `Retefuente [Mes]` y resumen

La pestaña se construye con:

- filas de datos a partir de las líneas de retención (concepto, base, base mínima, ¿supera la base?,
  tarifa, retención, observaciones);
- resumen final **por concepto** (base total, retención) y la fila final
  `TOTAL RETENCIÓN A DECLARAR`.

Las columnas nuevas empiezan en la columna **U** (la pestaña `Retefuente` se apoya en la copia de
`Compras`).

---

---

## D-47. C7 pasa a ser alerta y Total Neto resta otros impuestos (actualiza D-19 y D-24)

**Problema reportado:** con datos reales, C7 bloqueaba la exportación siempre que un documento
trajera ICA/INC/Timbre/etc. distinto de cero, aunque el Total sí cuadrara con sus componentes.

**Decisión (pendiente de aprobación del usuario):**

- C7 deja de ser `bloqueante` y pasa a **alerta**: si hay otros impuestos deriva `nivel=alerta`
  (amarilla en la interfaz). `ResultadoCuadre` expone `nivel` (`ok`/`alerta`/`error`) derivado de
  `ok`/`bloqueante`.
- `ResultadoProcesamiento.alertas` expone los cuadres en amarillo y
  `requiere_confirmacion_otros` indica si hay alguno. `puede_exportar` sigue ignorando alertas.
- `exportar_hoja(…, confirmar_otros_impuestos=False)`: si hay alerta y no se confirma, lanza
  `ConfirmacionRequerida` y no escribe archivo. La ventana pone casilla «Entiendo la diferencia y
  quiero exportar»; mientras no esté marcada, Exportar queda deshabilitado.
- El escritor agrega columna **U «Otros impuestos»** (suma de ICA..ICUI leída por el lector) y el
  Neto pasa a fórmula viva **`Total - IVA - Otros`** (`=R{fila}-P{fila}-U{fila}`); los totales
  suman U con `SUM`. `DocumentoElectronico.total_neto` y `ResultadoMes.total_neto` pasan a
  `Total - IVA - otros` en Python. La pestaña `Retefuente` se desplaza una columna a la derecha
  (V..AB) porque U queda ocupada.
- Cuando se exporta con confirmación, `Sumatorias!C1` lleva nota visible:
  *«NOTA: exportado con otros impuestos distintos de IVA confirmados por el usuario (ver C7)»*.
- Se mantiene bloqueo duro solo si el Total no cuadra con sus componentes (Neto negativo
  inexplicable o Total negativo): en ese caso C7 sigue siendo `bloqueante`.
- El golden de referencia #3 compara el Neto esperado como `Neto_referencia − otros`, y se verifica
  la nota y la confirmación.

**Estado:** aprobada por el usuario (2026-11-07).

---

---

## D-49. Pendientes sin confirmar, parámetros y conceptos nuevos (actualiza regla 5)

**Problema:** toda sugerencia era indistinguishable de una línea confirmada; el total decía
«A DECLARAR» aunque hubiera líneas pendientes, y el editor solo admitía los cinco conceptos.

**Decisión (pendiente de aprobación del usuario):**

- `LineaRetefuente.confirmada`: toda línea sugerida nace `confirmada=False` (pendiente).
  `confirmar_retefuente` las devuelve con `confirmada=True`. Ver TODO en el motor: la comparación
  de base mínima sigue siendo `>=` y **no se cambia** hasta confirmar con el contador
  (pregunta abierta: ¿`>=` o `>`?).
- Exportar con pendientes exige confirmación: `exportar_hoja(…, confirmar_pendientes=False)`
  lanza `ConfirmacionRequerida` y no escribe. La ventana pide con `QMessageBox` *«¿Quieres
  exportar igualmente como PROVISIONAL?»*. El botón «Confirmar retenciones y exportar» ya es la
  confirmación (exporta con `True` sin re-preguntar).
- La pestaña marca cada pendiente con *«PENDIENTE DE CONFIRMAR»* y relleno amarillo. La fila
  total dice *«TOTAL RETENCIÓN PROVISIONAL (N pendiente(s))»* si hay alguna, si no
  *«TOTAL RETENCIÓN A DECLARAR»*.
- La pestaña escribe parámetros usados bajo el resumen: año, UVT y base/tarifa de cada concepto.
  `RetefuenteMes` lleva `anio`, `uvt_pesos` y `conceptos` (foto de la configuración).
- El YAML y el editor admiten **conceptos nuevos** además de los cinco base (han de traer base y
  tarifa). Excepciones por proveedor (`no aplica` / `autorretenedor` / `no sujeto a retención`)
  se resuelven sin exigir entrada en la configuración: tarifa 0 y sin retención.

**Estado:** aprobada por el usuario (2026-11-07).

---

---

## D-50. Compras netas y ventas netas (fórmulas vivas)

**Decisión (pendiente de aprobación del usuario):**

- En `Sumatorias` y `Compras` se agrega **COMPRAS NETAS** `= TOTAL FACTURAS DE COMPRAS - TOTAL
  DEVOLUCIONES EN COMPRAS` en columnas P, Q, R y U (fórmula viva con celdas de totales).
- En `Sumatorias` y `Ventas`, si hay devoluciones en ventas, se agrega **VENTAS NETAS** de forma
  análoga.
- No cambia bloques ni signos (D-12) ni afecta C1–C7 (no es bloque).

**Estado:** aprobada por el usuario (2026-11-07).

---

---

## Resumen

| # | Decisión | Quién aprobó |
|---|---|---|
| D-01 | Nombre del archivo | usuario |
| D-04 | Literales canónicos | agente |
| D-05 | Orden DEVOLUCIONES EN VENTAS | pendiente |
| D-07 | Retefuente sin golden | agente |
| D-08 | Application response | usuario |
| D-09 | Documento equivalente | usuario |
| D-10 | Documento soporte recibido | usuario |
| D-11 | Estados incluidos | agente |
| D-12 | Signo notas crédito | usuario |
| D-15 | Prefijo NIT/CC | pendiente |
| D-17 | Mes sin documentos | usuario |
| D-18 | YAML/UVT 2026 | pendiente |
| D-19 | Impuestos ≠ IVA (bloqueo viejo) | pendiente |
| D-23 | Referencias anonimizadas | agente |
| D-24 | Referencia #3 INC (bloqueo viejo) | pendiente |
| D-31 | Botón exportar habilitado | agente |
| D-33 | Nombre pestaña Retefuente | agente |
| D-34 | Null = faltante | agente |
| D-35 | Pestaña Retefuente y resumen | agente |
| D-47 | C7 alerta + Otros impuestos | usuario |
| D-49 | Pendientes + parámetros + conceptos | usuario |
| D-50 | Compras/ventas netas | usuario |

**Pendientes:** D-05, D-15, D-18, D-19, D-24, D-47, D-49, D-50

