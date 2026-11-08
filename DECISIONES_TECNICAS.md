# Decisiones técnicas

Registro de decisiones de **implementación** (hilos, rutas, empaquetado, estilos, pruebas).
Las decisiones de negocio están en `DECISIONES.md`.

Convención: `R-A` = referencia de 52 documentos (oct), `R-B` = referencia de 53 (sep),
`R-C` = referencia de 89 (oct, la que usa `AGENTS.md` como fuente de verdad).

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

---

## D-03. Nombres de fórmulas dentro del `.xlsx`

La guía y `AGENTS.md` escriben `=SI(...)`, `=SUMAR.SI(...)`. Excel guarda las fórmulas en inglés;
`=SI(...)` escrito por openpyxl produce `#NAME?`.

**Propuesta:** el archivo lleva `SUM`, `IF`, `SUMIF`, `ROUND`. El español queda solo en la
documentación y en los mensajes al usuario.

**Estado:** aprobada (es un requisito técnico, no una preferencia).

---

---

## D-06. Estilo de las fórmulas de total

Las referencias mezclan tres estilos en el mismo archivo: `=P8`, `=SUM(P13:P96)` y `=P101+P102+P103`.

**Propuesta:** **siempre** `SUM` con rango, incluso para una sola fila: `=SUM(P8:P8)`.
Nunca sumas celda por celda (regla 12). El resultado numérico es idéntico, así que el golden
compara **valores**, no texto de fórmula.

**Estado:** aprobada.

---

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

---

## D-25. Fixture sintético generado en memoria

El listado de prueba no se versiona como `.xlsx` binario. `tests/herramientas/listado_sintetico.py`
lo construye con openpyxl y lo guarda en una carpeta temporal (`tmp_path`), con datos inventados.
Ventajas: no hay binarios opacos en el repositorio, se puede variar por prueba (duplicado, fecha
fuera de periodo, documento desconocido, otros impuestos) y se lee exactamente igual que un archivo
descargado de la DIAN.

---

---

## D-26. Cascada de C1, C2 y C4 con documentos sin clasificar

Cuando un documento queda en `SIN_CLASIFICAR`, además de C1 fallan C2 y C4: no llega a ningún
bloque, así que la suma de bloques ya no iguala el total de la DIAN. No es un defecto, es la
consecuencia correcta de no descartar nada.

**Decisión:** las pruebas afirman que C1 está entre los cuadres fallidos y que el documento aparece
en `no_clasificados`, sin exigir que sea el único código. La interfaz mostrará todos los cuadres
fallidos, no solo el primero.

---

---

## D-27. Corrección de estilos medidos

Al medir la referencia (D-16) se corrigieron tres detalles:

- El título general (`REVISION DEL TOTAL...`) va en **11 pt negrita**, no 13.
- Las celdas de dinero (IVA, Total Neto, Total) van en **11 pt**, un punto más que el resto de la fila.
- Los **anchos de columna son iguales en `Sumatorias`, `Ventas` y `Compras`**. La referencia los tenía
  inconsistentes entre pestañas; la app usa una sola tabla de anchos para que las tres se vean igual.

Todo esto es cosmético: el golden no compara fuentes, colores ni anchos (D-14).

---

---

## D-28. Celdas vacías `''` frente a `None` en la copia de `Dian`

La referencia guarda algunas celdas como **cadena vacía** (`''`) y otras como celda realmente vacía
(`None`). Al abrir y volver a guardar con openpyxl, las cadenas vacías quedan como `None`.

**Decisión:** el golden considera equivalentes `None` y `''` al comparar la pestaña `Dian`. Para
Excel son la misma celda vacía y no hay pérdida de información. Cualquier otro cambio de valor sí
falla la prueba.

---

---

## D-29. Prueba de recálculo real

`tests/test_recalculo.py` abre el archivo generado con LibreOffice en modo `--headless`, lo convierte
a `.xlsx` (forzando el recálculo) y verifica que no haya `#REF!`, `#VALUE!`, `#NAME?` ni errores
similares. También comprueba que los totales recalculados cuadren y que `Total Neto = Total − IVA`.

Si LibreOffice no está instalado, la prueba **se salta** con un mensaje explícito; no se simula el
resultado. En esta máquina no está instalado, así que hoy se ejecuta como `skip`.

---

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

---

## D-32. Cliente ingresado desde la interfaz por NIT

Hasta la Fase 3 no hay lista de clientes persistida (SQLite se incorpora en Fase 3).

**Decisión:** la ventana pide nombre y NIT al usuario; al procesar construye el `Cliente` con
`tipo_identificacion="NIT"`. Si el NIT está vacío no procesa. Esto mantiene la regla de que el NIT es
texto y se valida contra los documentos (C6) sin inventar datos.

---

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

---

## D-37. Perfiles por cliente en SQLite

`AGENTS.md` §9 pide «perfiles por cliente». La Fase 2 pedía nombre y NIT cada vez, sin memoria.

**Decisión:** se guardan en la tabla `perfiles_cliente` del SQLite local
(`~/.dian_hojas/retefuente.sqlite`): nombre, tipo y número de identificación, dígito de verificación
y carpeta de salida. El número se guarda como **texto** (regla 8), así conserva ceros a la izquierda.
La ventana trae un combo «Cliente guardado» y un botón «Guardar cliente»; al elegir un perfil se
rellenan los campos. Las reglas propias por cliente quedan reservadas en `reglas/clientes/`.

---

---

## D-38. Editor gráfico de la configuración tributaria

La regla 4 exige que UVT, bases mínimas y tarifas salgan **solo** de `reglas/[año].yaml`. Editar YAML
a mano excluye a usuarios sin conocimientos técnicos.

**Decisión:** la interfaz ofrece «Configuración tributaria…» con un formulario para el año, la UVT y
los cinco conceptos (base mínima en UVT y tarifa). Al guardar:

- se valida todo (valores presentes, numéricos, UVT > 0, base ≥ 0, 0 ≤ tarifa ≤ 1);
- si falta algo se muestra el error y **no se escribe** el archivo;
- se escribe con `guardar_configuracion` en `reglas/[año].yaml`, sin rellenar valores por defecto.

La tarifa se escribe como decimal (`0.05` = 5%), igual que la lee el motor.

---

---

## D-39. «Cargar YAML existente»

El usuario puede tener un YAML que le entregó su contador, con otro nombre o en otra carpeta.

**Decisión:** el botón «Cargar YAML existente…» lee y valida el archivo, y **muestra** sus valores en
el formulario. No lo copia automáticamente: se guarda solo cuando el usuario pulsa «Guardar», y en ese
momento queda en `reglas/[año].yaml`. El año se toma del propio archivo (`anio:`) y, si no lo trae, del
selector de la ventana.

---

---

## D-40. OCR opcional, nunca obligatorio

El usuario pidió explícitamente que no se obligue a incluir una factura en PDF o imagen.

**Decisión:** el OCR es un módulo **opcional** (`infraestructura/ocr.py`, protocolo `OcrProveedor`).

- La aplicación funciona completa sin `pytesseract` ni poppler.
- Solo se ejecuta si el usuario pulsa «Verificar soportes (OCR, opcional)…» y elige archivos.
- Si faltan las dependencias, el archivo no existe o no tiene texto, se lanza `ErrorOcr` y la
  interfaz muestra el aviso; el resto del flujo sigue.
- Las dependencias viven en el extra `[ocr]` del `pyproject.toml`.
- El motor real se importa dentro de la función, y `Ocr(motor=...)` permite probarlo sin Tesseract.

---

---

## D-41. Cruce con soportes físicos

El cruce automático solo debe ayudar, no bloquear ni adivinar.

**Decisión:** `documentos_en_texto` normaliza el texto (mayúsculas, sin tildes ni signos) y busca:

- el CUFE completo, o
- `prefijo + folio`, o
- un folio suelto de al menos 6 caracteres (para evitar falsos positivos con folios como `16`).

Los documentos encontrados se marcan con `FISICA = TRUE` en `Ventas`/`Compras` al exportar. Si el
cruce no encuentra nada, la exportación continúa igual: la columna `FISICA` es una ayuda de revisión,
no un cuadre obligatorio.

---

---

## D-42. Rutas de reglas y datos en fuente y en `.exe`

La ventana resolvía `reglas/` con `parents[3]`, que apuntaba a `src/reglas` y no a la raíz del
repositorio. Además, dentro de un ejecutable `__file__` vive en una carpeta temporal.

**Decisión:** `rutas.py` centraliza la resolución:

1. `DIAN_HOJAS_REGLAS` / `DIAN_HOJAS_DATOS` si están definidas;
2. si `sys.frozen`, `reglas/` al lado del `.exe` y datos en `~/.dian_hojas`;
3. en el repositorio, `reglas/` en la raíz.

Así el usuario puede editar sus reglas sin tocar el binario.

---

---

## D-43. Empaquetado con PyInstaller

`AGENTS.md` §9 pide empaquetado `.exe`.

**Decisión:** `dian_hojas.spec` construye una carpeta (`onedir`) llamada `HojasTrabajoDIAN`, con
entrada `python -m dian_hojas` (`__main__.py`). `scripts/construir_exe.ps1` instala los extras
`[gui,empaquetado]`, construye y copia `reglas/` al lado del ejecutable. Las reglas **no** se meten
dentro del binario (se perderían o quedarían ocultas para el usuario). El OCR se incluye solo si sus
módulos están instalados al construir.

---

## D-44. Reprocesar tras error de periodo sin cerrar la app

**Problema reportado:** si el periodo se eligía mal al inicio, la app mostraba «fuera del
periodo» y no se podía corregir sin cerrar y volver a abrir.

**Causa:** el procesamiento vive en un `QThread` propio. Al pulsar «Procesar» por segunda vez,
el hilo anterior seguía vivo y su resultado (con el periodo viejo) llegaba tarde y pisaba la
vista. Además, `sender()` no es fiable con conexiones entre hilos en PySide6.

**Decisión:** cada intento lleva un número de generación. Las señales `termino_generacion` y
`error_generacion` lo transportan y la ventana descarta todo lo que no coincida con la
generación vigente. `procesar()` limpia el estado previo, el botón «Procesar» se re-habilita y
`_refrescar()` muestra el error o el aviso de cuadres en rojo en lugar del texto «Mes procesado».

**Prueba:** `test_reprocesar_corrigiendo_el_periodo_sin_cerrar` procesa a septiembre (C5 en
rojo) y corrige a octubre (todo OK) en la misma ventana, sin cerrar.

---

---

## D-45. El botón «Examinar…» no mostraba el archivo descargado

**Problema reportado:** al pulsar «Examinar…» el archivo tampoco aparecía.

**Causa:** el diálogo filtraba solo `*.xlsx`. El archivo del usuario es
`3-Hoja de trabajo Rtefte Oct.2026.xlsm` (`.xlsm`), así que quedaba oculto. Además abría en
carpeta vacía en vez de en Descargas o en la última carpeta usada.

**Decisión:** el diálogo abre en la última carpeta usada o en Descargas, y acepta
`*.xlsx *.xlsm *.xls` (con el aviso de que `.xls` debe guardarse como `.xlsx`). La etiqueta se
aclaró: ya no dice «(.xlsx)» sino «(Excel descargado)» y avisa de que la hoja `.xlsm` también
sirve para probar, porque tiene la pestaña `Dian` idéntica al listado.

**Nota de uso:** la hoja de referencia `Referencias/3-*.xlsm` está anonimizada (NIT `x`,
documentos con INC distinto de cero), por eso con ella C6/C7 quedan en rojo aunque el listado
se lea bien. Para probar la exportación completa use `salidas/ejemplo/listado_sintetico.xlsx`
(NIT `900000001`, octubre 2026, 13 documentos, todo OK).

---

---

## D-46. Guía de datos tributarios sin mencionar «YAML»

**Problema reportado:** «está bastante complejo el tema del yaml».

**Decisión aprobada por el usuario (2026-11-07):** guía guiada sin YAML. La ventana ya no dice
«YAML» en ningún texto visible: se llama «Datos tributarios (contador)…», el botón es
«Cargar datos de tu contador…» y la ayuda dice en 3 pasos qué pedirle al contador y dónde
escribir cada dato. Internamente sigue siendo el mismo `reglas/[año].yaml`; solo se oculta la
jerga. Si el usuario no tiene los datos, la app exporta igual sin la pestaña `Retefuente` y lo
avisa en lenguaje simple.

---

---

## D-48. Prueba real de fórmulas sin skip en Windows (actualiza D-29 y D-14)

**Problema:** `tests/test_recalculo.py` se saltaba si LibreOffice no estaba, así que en CI
local nunca se comprobaba que las fórmulas vivas no dejaran `#REF!/#VALUE!/#NAME?` ni que el
Neto cuadrara.

**Decisión (pendiente de aprobación del usuario):**

- `tests/test_recalculo.py` localiza `soffice.exe` en este orden: variable `DIAN_HOJAS_SOFFICE`,
  PATH (`soffice`/`libreoffice`), rutas típicas de Windows (`C:\Program Files\LibreOffice\program`,
  `(x86)`, `LibreOffice 7/24`). Ver `README.md` para instalación.
- Si hay LibreOffice, recalcula de verdad en `--headless --convert-to xlsx` y comprueba errores
  y `Neto = Total - IVA - Otros` (D-47) sobre la caché.
- Si no hay LibreOffice, **no se salta**: evalúa las fórmulas del `.xlsx` en Python con el
  evaluador mínimo de las pruebas (y compara contra el modelo). La prueba negativa
  `test_respaldo_detecta_rango_corrido_una_fila` corrompe a propósito un `SUM` una fila y
  verifica que el respaldo lo detecta.
- El golden (D-14) ya comparaba valores evaluados desde el archivo con `valor()`; ahora también
  la prueba de recálculo lo hace con el respaldo, no solo con el modelo Python.

**Estado:** aprobada por el usuario (2026-11-07).

---

---

## D-51. Autofiltro solo documentos y salida sin sobrescribir (actualiza D-13)

**Decisión (pendiente de aprobación del usuario):**

- **Autofiltro:** en `Ventas`/`Compras` cubre `C4:U{última fila de datos}` (cabecera + documentos,
  sin totales ni netas finales). ¿Cómo se fijan te? En `Sumatorias`, con varios bloques, **no hay
  autofiltro**. La referencia tenía el filtro quedo (D-13) y mezclaba títulos/totales.
- **Sobrescritura:** `exportar_hoja` nunca sobrescribe en silencio. Si la salida existe, agrega
  `_v2`, `_v3`, … El listado de entrada nunca se sobrescribe (el escritor ya lanza si coinciden).

**Estado:** aprobada por el usuario (2026-11-07).

---

---

## D-52. NIT sin dígito de verificación en C6

**Decisión (pendiente de aprobación del usuario):**

- C6 compara `Cliente.numero_digitos` contra NIT emisor/receptor quitando en ambos lados
  puntos, guiones y el dígito de verificación (`900000001-1` = `900000001`).
- La ventana tiene selector **NIT/CC** que fluye a `Cliente.tipo_identificacion`, al encabezado
  (`NIT. …` / `CC. …`) y al perfil guardado, coherente con D-32 y D-37.

**Estado:** aprobada por el usuario (2026-11-07).

---

---

## D-53. Windows: QStandardPaths, pathlib y empaquetado (actualiza D-45)

**Decisión (pendiente de aprobación del usuario):**

- El sistema destino es **Windows 10/11**. Se quitan menciones a macOS en código y documentos.
- «Examinar…» usa `QStandardPaths.DownloadLocation` (descarga real de Windows) con solo
  `pathlib`; ya no usa `ctypes SHGetKnownFolderPath` ni rutas duras `C:`/`D:`.
- `dian_hojas.spec` es `onedir` para Windows 10/11; `reglas/` se copia junto a
  `HojasTrabajoDIAN.exe` (no dentro del binario).
- README documenta Python 3.12, cómo construir el `.exe`, falsos positivos del antivirus por
  PyInstaller y que `~/.dian_hojas/retefuente.sqlite` (NIT/nombres) no debe sincronizarse ni
  subirse al repo. No se registran NIT/nombres en logs.

**Estado:** aprobada por el usuario (2026-11-07).

---

## D-54. Se quita la tabla de Excel de `Dian` al copiar (actualiza D-21)

**Problema:** el listado de la DIAN (exportado vía Google Sheets) trae una tabla de Excel
con estilo `Dian-style`. Al guardar como `.xlsx` con openpyxl, Excel rechaza el archivo
(`<tableParts>` huérfano + `definedNames` duplicado + filas vacías `t="n"`).

**Decisión (pendiente de aprobación del usuario):**

- En la copia de `Dian` se borra la tabla (`_tables`), se limpian `FilterDatabase` duplicados,
  vistas huérfanas y filas vacías con formato (91–1000). Los datos `1..N`, el autofiltro y el
  panel fijo quedan intactos; el original no se toca.
- Verificado con Excel COM: el archivo generado desde el `.xlsm` real ya abre sin el aviso.

**Estado:** pendiente de aprobación del usuario.

---

## Resumen

| # | Decisión | Quién aprobó |
|---|---|---|
| D-02 | DIAN/FISICA | pendiente |
| D-03 | Fórmulas en inglés | agente |
| D-06 | SUM con rango | agente |
| D-13 | Rango del autofiltro | pendiente |
| D-14 | Golden | agente |
| D-16 | Estilos visuales | agente |
| D-20 | Privacidad y fixtures | agente |
| D-21 | Copia Dian reutilizando libro | agente |
| D-22 | Orden y golden multiconjunto | agente |
| D-25 | Fixture sintético en memoria | agente |
| D-26 | Cascada C1/C2/C4 | agente |
| D-27 | Estilos medidos | agente |
| D-28 | '' vs None | agente |
| D-29 | Recálculo LibreOffice | pendiente |
| D-30 | QThread | agente |
| D-32 | Cliente por NIT | agente |
| D-36 | Tabla editable retención | agente |
| D-37 | Perfiles SQLite | agente |
| D-38 | Editor gráfico | agente |
| D-39 | Cargar YAML existente | agente |
| D-40 | OCR opcional | agente |
| D-41 | Cruce soportes | agente |
| D-42 | Rutas reglas/datos | agente |
| D-43 | Empaquetado onedir | agente |
| D-44 | Reprocesar sin cerrar (hilo) | agente |
| D-45 | Examinar archivos y Descargas | agente |
| D-46 | Guía sin YAML | usuario |
| D-48 | Fórmulas sin skip Windows | usuario |
| D-51 | Autofiltro solo docs + no sobrescribir | usuario |
| D-52 | NIT sin DV en C6 | usuario |
| D-53 | Windows QStandardPaths + pathlib | usuario |
| D-54 | Sin tabla Excel en Dian | pendiente |

**Pendientes:** D-02, D-13, D-29, D-54

