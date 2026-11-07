# Decisiones de diseño

Registro de decisiones tomadas al revisar `AGENTS.md`, la guía y las **tres hojas de referencia**.
Cada punto tiene una propuesta concreta. Los marcados **⚠ pendiente** necesitan tu aprobación
antes de escribir el código de la Fase 1.

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

## D-02. Columnas A/B (`DIAN` / `FISICA`) en `Ventas` y `Compras`

`AGENTS.md` habla de celdas booleanas; la guía habla de "casillas de verificación".
En las referencias son **valores booleanos** en A y B (encabezados en A5/B5), no controles de formulario.

**Propuesta:** escribir `TRUE`/`FALSE` reales (no checkbox). Al generar:

- `DIAN = TRUE` (el documento viene del listado, por definición).
- `FISICA = FALSE` (queda pendiente de que el usuario lo verifique contra el soporte).

Las referencias traen combinaciones humanas (`FALSE/FALSE`, `FALSE/TRUE`), así que **la comparación
golden ignora las columnas A y B**.

**Estado:** aprobada por defecto (propuesta adoptada). Si prefieres `FALSE/FALSE` y que el usuario
marque todo, se cambia en una línea.

---

## D-03. Nombres de fórmulas dentro del `.xlsx`

La guía y `AGENTS.md` escriben `=SI(...)`, `=SUMAR.SI(...)`. Excel guarda las fórmulas en inglés;
`=SI(...)` escrito por openpyxl produce `#NAME?`.

**Propuesta:** el archivo lleva `SUM`, `IF`, `SUMIF`, `ROUND`. El español queda solo en la
documentación y en los mensajes al usuario.

**Estado:** aprobada (es un requisito técnico, no una preferencia).

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

## D-05. Orden de los bloques en `Sumatorias`

`AGENTS.md` lista `DEVOLUCIONES EN VENTAS` al final ("si hay"). `R-A`, que es la única que tiene ese
bloque, lo pone **inmediatamente después de ventas**.

**Propuesta:** `VENTAS` → `DEVOLUCIONES EN VENTAS` (si hay) → `COMPRAS` → `DEVOLUCIONES EN COMPRAS` → `NOMINA`.

**Estado:** aprobada por defecto (propuesta adoptada, la referencia real manda sobre la tabla del `.md`).

---

## D-06. Estilo de las fórmulas de total

Las referencias mezclan tres estilos en el mismo archivo: `=P8`, `=SUM(P13:P96)` y `=P101+P102+P103`.

**Propuesta:** **siempre** `SUM` con rango, incluso para una sola fila: `=SUM(P8:P8)`.
Nunca sumas celda por celda (regla 12). El resultado numérico es idéntico, así que el golden
compara **valores**, no texto de fórmula.

**Estado:** aprobada.

---

## D-07. Pestaña `Retefuente [Mes]`

Ninguna de las tres referencias tiene esa pestaña: las hojas reales terminan en `Compras`.
No hay golden file para Retefuente.

**Propuesta:** en Fase 3 la pestaña se valida con pruebas unitarias del motor y con una revisión
tuya sobre un caso real; no se compara contra referencia. Y cuando tengamos una hoja con Retefuente
ya trabajada, se agrega como cuarta referencia.

**Estado:** informativa.

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

## D-09. Tipo `Documento equivalente`

El nombre real es `Documento equivalente - Servicios públicos domiciliarios`, no
`Documento equivalente`. Comparar por igualdad exacta lo mandaría a `SIN_CLASIFICAR`.

**Propuesta:** el clasificador compara **normalizado** (sin tildes, minúsculas, espacios colapsados)
y por **prefijo** para `documento equivalente`. Igual criterio para `documento soporte`
(`Documento soporte con no obligados`).

**Estado:** aprobada.

---

## D-10. `Documento soporte` con Grupo `Recibido`

`AGENTS.md` solo contempla `Documento soporte` + `Emitido` → `COMPRA`. `R-B` trae uno **recibido**
y el proceso manual lo metió en `Compras`.

**Propuesta:** `Documento soporte` → `COMPRA` con **cualquiera** de los dos grupos.
La columna `Grupo` se conserva y el cuadre 6 (identificación del cliente) se resuelve por
emisor **o** receptor, sin exigir cuál.

**Estado:** aprobada. Ambos grupos van a `COMPRA` y se conserva la columna `Grupo`.

---

## D-11. Estado del documento

En las referencias solo aparecen `Aprobado` y `Aprobado con notificación`, y **ambos se incluyen**.

**Propuesta:** incluir los dos. Cualquier otro estado queda en `SIN_CLASIFICAR` con alerta
(no se descarta).

**Estado:** aprobada.

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

## D-13. Rango del autofiltro

En las referencias el autofiltro quedó desactualizado: `R-C` filtra `C4:T102` con datos hasta la
fila 109; `R-B` filtra `C4:T70` (correcto); `R-A` filtra `C4:T65` con datos hasta 78.
Además el rango incluye filas de título y de total, que el filtro ocultaría.

**Propuesta:** generar `C4:T{última fila con datos}` (incluye totales, igual que la referencia, para
no inventar un comportamiento distinto) y **recalcularlo siempre**. El golden compara solo celda
inicial y presencia del filtro, no la fila final.

**Estado:** aprobada por defecto. Alternativa si prefieres: filtrar solo la tabla de documentos,
dejando fuera títulos y totales — más limpio, pero se aparta de la referencia.

---

## D-14. Cómo se compara contra la referencia (golden)

Comparar texto de fórmula es frágil (D-06) y las columnas A/B son marcas humanas (D-02).

**Propuesta:** la prueba de integración compara, hoja por hoja:

1. Nombre y orden de las pestañas.
2. Encabezados de fila 4 (C..T) y celdas combinadas normalizadas a `E1:S1`, `E2:S2`, `E3:S3`.
3. Secuencia de filas: tipo (título de bloque / datos / total) y etiqueta de cada fila.
4. Valores numéricos de P, Q y R por fila y por total de bloque.
5. Texto de las celdas de datos C..T (incluye CUFE, folio, fechas, nombres).
6. `freeze_panes` y celda inicial del autofiltro.

Ignora: columnas A/B, texto exacto de fórmulas, anchos, colores y la fila 1000 vacía de `Dian`.

**Estado:** aprobada.

---

## D-15. Encabezado de las filas 1–3

`R-A` y `R-C` combinan `E1:S1`, `E2:S2`, `E3:S3`; `R-B` combina `D1:V1` (error manual) y su fila 2
dice `1.020.434.199` sin el prefijo `NIT.`.

**Propuesta:** siempre `E1:S1` / `E2:S2` / `E3:S3`, con:

- Fila 1: nombre del cliente.
- Fila 2: `NIT. 901.320.747-4` (con puntos de miles y dígito de verificación si existe);
  para persona natural, `CC. 1.020.396.459`.
- Fila 3: `LISTADO DOCUMENTOS ELECTRONICOS DIAN {MES} {AÑO}` en mayúsculas y sin doble espacio.

**Estado:** aprobada por defecto solo en el prefijo `NIT.` / `CC.`.

---

## D-16. Estilos visuales

Medidos en `R-C`:

- Encabezado (fila 4): negrita, Calibri 10, texto blanco, relleno `#348441`, centrado.
- Título general y títulos de bloque: negrita, relleno `#DBE5F1`; el título general de `Sumatorias`
  a 13 pt.
- Columnas P, Q, R: formato `"$"\ #,##0;[Red]\-"$"\ #,##0` (moneda sin decimales).
- Anchos (C..T): `8.7, 13, 13, 13, 13, 13, 13, 13, 13, 13, 35.6, 8.7, 35.6, 12.1, 13.9, 12.7, 8.7, 13`.

**Propuesta:** fijar estos valores en el escritor como constantes de estilo. El golden no los compara
(son cosméticos), pero así la salida se ve igual a la hoja que ya usas.

**Estado:** aprobada.

---

## D-17. Mes sin movimiento

La guía dice "no crees pestañas vacías sin necesidad", pero el estándar de salida son 5 pestañas.

**Propuesta:** si el listado viene sin filas, la app **no exporta**: muestra el aviso
"El listado del mes no tiene documentos" y deja al usuario decidir. Es más honesto que un archivo
vacío que luego se confunde con un mes trabajado.

**Estado:** aprobada. Si el listado no trae filas, no se genera archivo y se avisa.

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

## D-19. Impuestos distintos de IVA

`AGENTS.md` conserva solo `IVA` y `Total`. Si en un mes `ICA`, `INC`, `Timbre` o similares vienen
distintos de cero, `Total Neto = Total − IVA` deja de ser el valor antes de IVA y el cuadre se
degrada sin avisar.

**Propuesta:** validar al leer. Si la suma de impuestos distintos de IVA es ≠ 0, la app **no exporta**
y muestra la lista de documentos afectados. Es preferible a un neto silenciosamente incorrecto.

**Estado:** aprobada. Si la suma es distinta de cero, la app no exporta y lista los documentos
afectados. Cuadre C7.

---

## D-20. Privacidad y fixtures

Regla 10: nunca datos reales en el repositorio.

**Propuesta:**

- `Referencias/` va en `.gitignore` (ya está) y nunca se versiona.
- `tests/fixtures/` solo lleva archivos **sintéticos** o **anonimizados**.
- La prueba golden contra las tres referencias reales existe, pero está marcada `@referencias` y
  se salta sola si la carpeta no está (por ejemplo en otra máquina o en CI).

**Estado:** aprobada.

---

## D-21. Conservar `Dian` reutilizando el libro original

Copiar la hoja celda por celda es frágil: se pierden estilos, anchos, combinaciones, validaciones y
detalles que openpyxl no expone con comodidad.

**Decisión:** el escritor **abre el listado original**, borra las demás hojas, renombra la primera
como `Dian`, limpia `defined_names` y `_external_links` (apuntaban a hojas borradas y producirían
`#REF!`), marca `calculation.fullCalcOnLoad = True` y guarda. Así la pestaña queda intacta de verdad.
El listado de entrada nunca se sobrescribe: el escritor falla si `destino` es el mismo archivo.

**Efecto secundario aceptado:** al releer el `.xlsx`, openpyxl convierte las cadenas vacías `''` en
`None` (D-28). Para Excel ambas son celdas vacías.

---

## D-22. Orden de los documentos y comparación golden

`AGENTS.md` pide orden por fecha de emisión descendente en `Compras`, pero la hoja de referencia no
lo cumple de forma estricta y `Sumatorias` tampoco sigue el orden del listado.

**Decisión:**

- La app **sí** ordena cada bloque por `fecha_emision` descendente, con orden estable por índice del
  listado cuando hay fechas iguales. Es el criterio único de la sección 4.4.
- El golden **no** compara orden de filas: compara los documentos de cada bloque como
  **multiconjunto** (mismo contenido, cualquier orden). Comparar el orden haría fallar la prueba por
  una diferencia que `AGENTS.md` no exige y que la referencia tampoco respeta.

---

## D-23. Las referencias están anonimizadas

En las tres hojas de `Referencias/`, las columnas de NIT y nombres de los documentos vienen como
`x`. La cabecera de `Sumatorias` de la referencia #3 sí conserva el cliente real
(`JHONY WALTER CHAVARRIA BETANCOURT`, `NIT. 1.020.396.459`); las referencias #1 y #2 no traen
cabecera.

**Consecuencia:** el cuadre C6 («el cliente aparece en el listado») **no se puede validar** sobre
estas referencias, porque la identificación real no existe en los datos. La prueba golden:

- lee el cliente de la cabecera cuando está; si no, usa un cliente de prueba,
- comprueba que C6 falla con un detalle claro (es lo correcto: el dato no está),
- valida C1 a C5, que sí son independientes de los NIT.

No se relaja la regla C6 ni se inventan NIT para que pase.

---

## D-24. La referencia #3 trae dos facturas con impuestos distintos de IVA

La referencia #3 contiene dos documentos reales con impuesto distinto de IVA:

| Documento | Impuesto | Valor |
|---|---|---|
| `05LB-235797` | INC Bolsas | 219,00 |
| `FCPT-35167450` | INC | 220,53 |

Aplicando D-19, la app **bloquea la exportación** de ese mes y lista ambos documentos. Es el
comportamiento pedido, aunque la hoja de referencia se haya preparado a mano sin corregirlo.

**Decisión para el golden:** la comparación estructural se hace llamando al escritor directamente,
sin pasar por `exportar_hoja` (que aquí bloquea a propósito). La prueba además verifica que:

- C7 falla y menciona exactamente esos dos folios y sus valores,
- `puede_exportar` es `False` y los cuadres fallidos son exactamente `{C6, C7}`.

Así se demuestra que la estructura coincide **y** que la app se niega a exportar en silencio.

---

## D-25. Fixture sintético generado en memoria

El listado de prueba no se versiona como `.xlsx` binario. `tests/herramientas/listado_sintetico.py`
lo construye con openpyxl y lo guarda en una carpeta temporal (`tmp_path`), con datos inventados.
Ventajas: no hay binarios opacos en el repositorio, se puede variar por prueba (duplicado, fecha
fuera de periodo, documento desconocido, otros impuestos) y se lee exactamente igual que un archivo
descargado de la DIAN.

---

## D-26. Cascada de C1, C2 y C4 con documentos sin clasificar

Cuando un documento queda en `SIN_CLASIFICAR`, además de C1 fallan C2 y C4: no llega a ningún
bloque, así que la suma de bloques ya no iguala el total de la DIAN. No es un defecto, es la
consecuencia correcta de no descartar nada.

**Decisión:** las pruebas afirman que C1 está entre los cuadres fallidos y que el documento aparece
en `no_clasificados`, sin exigir que sea el único código. La interfaz mostrará todos los cuadres
fallidos, no solo el primero.

---

## D-27. Corrección de estilos medidos

Al medir la referencia (D-16) se corrigieron tres detalles:

- El título general (`REVISION DEL TOTAL...`) va en **11 pt negrita**, no 13.
- Las celdas de dinero (IVA, Total Neto, Total) van en **11 pt**, un punto más que el resto de la fila.
- Los **anchos de columna son iguales en `Sumatorias`, `Ventas` y `Compras`**. La referencia los tenía
  inconsistentes entre pestañas; la app usa una sola tabla de anchos para que las tres se vean igual.

Todo esto es cosmético: el golden no compara fuentes, colores ni anchos (D-14).

---

## D-28. Celdas vacías `''` frente a `None` en la copia de `Dian`

La referencia guarda algunas celdas como **cadena vacía** (`''`) y otras como celda realmente vacía
(`None`). Al abrir y volver a guardar con openpyxl, las cadenas vacías quedan como `None`.

**Decisión:** el golden considera equivalentes `None` y `''` al comparar la pestaña `Dian`. Para
Excel son la misma celda vacía y no hay pérdida de información. Cualquier otro cambio de valor sí
falla la prueba.

---

## D-29. Prueba de recálculo real

`tests/test_recalculo.py` abre el archivo generado con LibreOffice en modo `--headless`, lo convierte
a `.xlsx` (forzando el recálculo) y verifica que no haya `#REF!`, `#VALUE!`, `#NAME?` ni errores
similares. También comprueba que los totales recalculados cuadren y que `Total Neto = Total − IVA`.

Si LibreOffice no está instalado, la prueba **se salta** con un mensaje explícito; no se simula el
resultado. En esta máquina no está instalado, así que hoy se ejecuta como `skip`.

---

## D-30. Procesamiento en `QThread` desde la ventana

El procesamiento de un listado puede tardar (lectura, clasificación, cuadres) y no debe bloquear la
interfaz. La ventana principal (`VentanaPrincipal`) arranca un `QThread` con un trabajador
`HiloProcesar` (un `QObject` con señales `termino`, `error` y `finished`) y lo conecta:

- `started → trabajador.trabajar`
- `trabajador.termino → ventana._on_termino` (slot de la GUI → conexión en cola)
- `trabajador.error → ventana._on_error`
- `trabajador.finished → hilo.quit`; `hilo.finished → hilo.deleteLater`

**Decisión:** el worker emite `termino` y luego `finished` en un bloque `finally`, para que el hilo
nunca quede colgado aunque falle la lectura.

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

## D-32. Cliente ingresado desde la interfaz por NIT

Hasta la Fase 3 no hay lista de clientes persistida (SQLite se incorpora en Fase 3).

**Decisión:** la ventana pide nombre y NIT al usuario; al procesar construye el `Cliente` con
`tipo_identificacion="NIT"`. Si el NIT está vacío no procesa. Esto mantiene la regla de que el NIT es
texto y se valida contra los documentos (C6) sin inventar datos.

---

## D-33. Nombre de la pestaña `Retefuente`

`AGENTS.md` §4.5 la llama `Retefuente [Mes]`, con ejemplo `Retefuente Octubre`.

**Decisión:** el nombre real de la pestaña generada es `Retefuente {Mes en nombre propio}`, por
ejemplo `Retefuente Octubre` para octubre. Se aplica `capitalize()` al nombre completo del mes
(`OCTUBRE` → `Octubre`).

---

## D-34. Valores ausentes en la configuración tributaria se consideran faltantes

Un YAML puede traer claves con valor `null`. Para los datos tributarios (UVT, base mínima, tarifa)
un valor `null` se trata como **ausente** y dispara el error de configuración con el concepto
incompleto.

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

## D-36. Tabla editable de retención en la interfaz

La Fase 3 dejó lista la capa de negocio (`sugerir_retefuente`, `confirmar_retefuente`) y el escritor de
la pestaña `Retefuente`, pero la **vista** no se conectaba todavía: faltaba la tabla editable que liste
las compras con su sugerencia (concepto, base, mínima, ¿supera?, tarifa, retención, observaciones) y un
botón de confirmar.

**Decisión:** la ventana principal llena la tabla desde el resultado del procesamiento y, al confirmar,
persiste las decisiones en el repositorio (proveedor → concepto) y reexporta la hoja con el resultado
confirmado.

---

## Resumen de lo que necesito de ti

| # | Decisión | Estado |
|---|---|---|
| D-01 | Nombre del archivo | aprobada (ejemplo de `AGENTS.md`) |
| D-02 | ¿La app marca `DIAN=TRUE` o deja ambas en `FALSE`? | aprobada por defecto: `TRUE/FALSE` |
| D-03 | Fórmulas en inglés dentro del `.xlsx` | aprobada |
| D-04 | Literales canónicos de bloques y totales | aprobada |
| D-05 | Orden de `DEVOLUCIONES EN VENTAS` | aprobada por defecto: junto a ventas |
| D-06 | Siempre `SUM` con rango | aprobada |
| D-07 | `Retefuente` sin golden file | informativa |
| D-08 | `Application response` | **aprobada**: categoría propia, excluida y reportada |
| D-09 | `Documento equivalente` por prefijo | aprobada |
| D-10 | `Documento soporte` recibido | **aprobada**: compra en ambos grupos |
| D-11 | Estados incluidos | aprobada |
| D-12 | Signo de las notas crédito | aprobada (confirmada con la referencia) |
| D-13 | Rango del autofiltro | aprobada por defecto: `C4:T{última}` |
| D-14 | Criterio de comparación golden | aprobada |
| D-15 | Prefijo `NIT.` / `CC.` | aprobada por defecto |
| D-16 | Estilos visuales | aprobada |
| D-17 | Mes sin documentos | **aprobada**: no exportar y avisar |
| D-18 | YAML de UVT, bases y tarifas 2026 | ⚠ **pendiente** — bloquea solo la Fase 3 |
| D-19 | Impuestos distintos de IVA ≠ 0 | **aprobada**: bloquear la exportación |
| D-20 | Privacidad y fixtures | aprobada |
| D-21 | Copia de `Dian` reutilizando el libro original | aprobada |
| D-22 | Orden por fecha y golden como multiconjunto | aprobada |
| D-23 | Referencias anonimizadas: C6 no se puede validar | aprobada |
| D-24 | Referencia #3 con INC real: C7 bloquea | aprobada |
| D-25 | Fixture sintético generado en memoria | aprobada |
| D-26 | Cascada C1/C2/C4 con `SIN_CLASIFICAR` | aprobada |
| D-27 | Corrección de estilos medidos | aprobada |
| D-28 | `''` y `None` equivalentes en la copia de `Dian` | aprobada |
| D-29 | Recálculo con LibreOffice (se salta si no está) | aprobada |
| D-30 | Procesamiento en `QThread` desde la ventana | aprobada |
| D-31 | Botón de exportación solo habilitado si el mes puede exportarse | aprobada |
| D-32 | Cliente ingresado desde la interfaz por NIT | aprobada |
| D-33 | Nombre de la pestaña `Retefuente` | aprobada |
| D-34 | Valores ausentes en la configuración tributaria se consideran faltantes | aprobada |
| D-35 | Pestaña `Retefuente [Mes]` y resumen | aprobada |
| D-36 | Tabla editable de retención en la interfaz | aprobada |

Lo único que sigue abierto es el YAML tributario de 2026 (D-18), y no hace falta hasta la Fase 3.
