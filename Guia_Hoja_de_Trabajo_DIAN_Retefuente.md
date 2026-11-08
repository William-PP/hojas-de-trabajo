# Guía general: hoja de trabajo mensual DIAN y retención en la fuente

Esta guía aplica a **cualquier cliente** (persona natural o empresa) y a cualquier mes. Se construyó con el flujo explicado y con la estructura real de una hoja ya trabajada (octubre 2026), de la que se tomó el orden de secciones, las fórmulas y las convenciones.

**Resultado final por cliente y mes:** un solo archivo Excel con estas pestañas, en este orden:

`Dian` | `Sumatorias` | `Ventas` | `Compras` | `Retefuente [Mes]`

---

## 0. Antes de empezar

### Datos que necesitas por cliente
| Dato | Para qué |
|---|---|
| Tipo y número de identificación (cédula o NIT) | Ingresar a la DIAN |
| NIT y cédula del representante legal (si es empresa) | Ingresar a la DIAN |
| Correo registrado en la DIAN (acceso al buzón) | Recibir el link de acceso |
| Acceso a Google Drive, carpeta del cliente | Guardar el archivo |
| Mes y año a trabajar | Filtrar el listado |

### Recomendaciones
- Ten el correo del cliente abierto **antes** de pedir el link: la sesión dura aprox. **1 hora**.
- Trabaja un cliente a la vez para no mezclar links ni descargas.
- Usa una sola convención de nombre de archivo (ver sección 3).

---

## 1. Descargar el listado desde la DIAN

### 1.1 Acceso a la plataforma
1. Entra a `https://www.dian.gov.co/`.
2. Baja hasta la parte inferior de la página y selecciona **"Facturando Electrónicamente"**.

### 1.2 Autenticación
**Si es empresa**
1. Selecciona **Empresa** → **Representante legal**.
2. Ingresa: tipo de identificación, NIT del representante legal y NIT de la empresa.

**Si es persona natural**
1. Selecciona **Persona**.
2. Ingresa: tipo de identificación y cédula del contribuyente.

### 1.3 Confirmación por correo
1. Revisa el correo registrado y abre el link que llegó (revisa también spam).
2. Tienes **aprox. 1 hora** para descargar. Si se vence, repite el paso 1.2.

### 1.4 Generar y descargar el reporte
1. En el menú de la izquierda: **Histórico** → **Descarga de listados**.
2. Elige el **mes y año** requeridos.
3. Selecciona el rango **del día 1 al día 31** (siempre en el selector del lado izquierdo, aunque el mes tenga menos días).
4. Clic en **Exportar Excel** y espera.
5. Cuando termine, aparece la exportación en la **tabla inferior**; descárgala desde ahí.

### Checklist de la descarga
- [ ] El archivo corresponde al **cliente** correcto (revisa el NIT en las columnas Emisor/Receptor).
- [ ] El archivo corresponde al **mes y año** correctos (revisa las fechas de emisión).
- [ ] Se abre sin errores y tiene filas.

> **Si el mes no tiene movimiento**, el archivo puede venir vacío: deja constancia en la carpeta y no crees pestañas vacías sin necesidad.

---

## 2. Qué trae el archivo de la DIAN

Una tabla de **32 columnas** (A a AF). Las que más se usan:

| Columna | Campo | Uso |
|---|---|---|
| A | Tipo de documento | Clasifica el documento (ver 2.1) |
| C / D | Folio / Prefijo | Identificar y cruzar con la factura física |
| H | Fecha de emisión | Orden y verificación del mes |
| J / K | NIT / Nombre del emisor | Quién vende |
| L / M | NIT / Nombre del receptor | Quién compra |
| N | IVA | Base para calcular el valor neto |
| AA / AB / AC | Rete IVA / Rete Renta / Rete ICA | Retenciones que ya vengan informadas |
| AD | Total | Valor total del documento |
| AE | Estado | Aprobado / Aprobado con notificación |
| AF | **Grupo** | **Emitido** (lo emitió el cliente) o **Recibido** (se lo emitieron al cliente) |

### 2.1 Tipos de documento que aparecen y a dónde va cada uno

| Tipo de documento | Grupo | Va a la sección |
|---|---|---|
| Factura electrónica | Emitido | **Ventas** |
| Factura electrónica | Recibido | **Compras** |
| Documento soporte con no obligados a facturar | Emitido | **Compras** (es una compra a alguien no obligado a facturar, la genera el cliente) |
| Documento equivalente (p. ej. servicios públicos domiciliarios) | Recibido | **Compras** |
| Nota de crédito electrónica | Recibido | **Devoluciones en compras** |
| Nota de crédito electrónica | Emitido | **Devoluciones en ventas** (si existen) |
| Nómina individual electrónica | Emitido | **Nómina** |

> **Regla práctica:** primero mira el **Grupo** (Emitido/Recibido) y luego el **Tipo de documento**. El grupo "Emitido" no siempre significa venta: el documento soporte y la nómina son "Emitidos" pero son costos/gastos del cliente.

---

## 3. Guardar el archivo en Google Drive

1. Entra a Drive y busca la carpeta de la **empresa o persona** correspondiente.
2. Abre **Asuntos Tributarios**.
3. Abre **Hojas de Trabajo**.
4. Abre **Mensual** y entra a la carpeta del **año** correspondiente.
5. Sube el archivo.

**Nombre sugerido** (el mismo patrón que ya se usa):

```
[N°]-Hoja_de_trabajo_Rtefte_[Mes]_[Año]_[Nombre_Cliente].xlsx
```
Ejemplo: `10-Hoja_de_trabajo_Rtefte_Oct_2026_Nombre_Cliente.xlsx`
(el número inicial es el número del mes, así las hojas quedan ordenadas en la carpeta).

> **Importante:** sube y trabaja sobre una **copia**. La pestaña `Dian` conserva el original.

---

## 4. Estructurar las pestañas

Regla general: se trabaja **de izquierda a derecha**, duplicando la pestaña anterior y depurándola.

```
Dian  →  Sumatorias  →  Ventas  →  Compras  →  Retefuente [Mes]
```

### 4.1 Pestaña `Dian` (original, intocable)
- Es el archivo exactamente como lo entregó la DIAN.
- **No se modifica nada**: ni orden, ni formato, ni columnas, ni filas.
- Es la fuente de verdad para cualquier revisión posterior.
- Tip: antes de duplicarla, anota el **número total de filas** (en el ejemplo: 89 documentos). Ese número debe cuadrar al final.

### 4.2 Pestaña `Sumatorias`
**Objetivo:** tener **todos** los documentos agrupados por tipo, con sus totales, para verificar que no se perdió ni se duplicó nada.

**Cómo se arma**
1. Duplica `Dian` y renómbrala `Sumatorias`.
2. Inserta **2 columnas** a la izquierda (queda un margen de A:B) para que la tabla empiece en la columna C.
3. En las filas 1 a 3, combina celdas (E:S) y escribe el encabezado:
   - Fila 1: **Nombre del cliente**
   - Fila 2: **NIT** (formato `NIT. 900.000.001-1`)
   - Fila 3: **LISTADO DOCUMENTOS ELECTRONICOS DIAN [MES] [AÑO]**
4. Fila 4: encabezados de la tabla (columnas C a T):

   `Tipo de documento | CUFE/CUDE | Folio | Prefijo | Divisa | Forma de Pago | Medio de Pago | Fecha Emisión | Fecha Recepción | NIT Emisor | Nombre Emisor | NIT Receptor | Nombre Receptor | IVA | Total Neto | Total | Estado | Grupo`

5. Elimina las columnas que no se usan (ICA, IC, INC, Timbre, etc., si están en cero), **dejando solo IVA y Total**, y agrega **Total Neto**.
6. Columna **Total Neto** = Total − IVA. Fórmula (ejemplo fila 8):

   ```
   =R8-P8
   ```
7. Fija el panel en `A5` (Inmovilizar paneles) y activa el **autofiltro** sobre el encabezado.
8. Organiza los documentos en bloques, cada uno con su título y su fila de total:

| Orden | Bloque | Contenido |
|---|---|---|
| 1 | **REVISION DEL TOTAL DE DOCUMENTOS Y SUMATORIAS** | Título general (fila 5) |
| 2 | **FACTURAS DE VENTAS** | Facturas electrónicas **emitidas** |
| 3 | **FACTURAS DE COMPRAS** | Facturas **recibidas**, documento soporte y documentos equivalentes |
| 4 | **DEVOLUCIONES EN COMPRAS** | Notas crédito recibidas |
| 5 | **NÓMINA** | Nómina individual electrónica |
| (si aplica) | **DEVOLUCIONES EN VENTAS** | Notas crédito emitidas |

9. Cada bloque cierra con una fila **TOTAL …** (en la columna O la etiqueta; en P, Q y R los totales):

| Bloque | Fórmula del total (ejemplo) |
|---|---|
| Un solo documento | `=P8` |
| Varios documentos seguidos | `=SUM(P13:P96)` |
| Pocos documentos | `=P101+P102+P103` |

> Prefiere siempre `SUM` con rango; la suma celda por celda se rompe si agregas una fila.

**Control de cuadre (obligatorio)**
- [ ] Cantidad de filas de todos los bloques **=** cantidad de filas de la pestaña `Dian`.
- [ ] Suma de los totales de todos los bloques **=** suma de la columna **Total** de `Dian`.
- [ ] Ningún documento aparece en dos bloques.

Si no cuadra: busca duplicados (mismo CUFE), documentos sin clasificar o filas que quedaron fuera del rango del `SUM`.

### 4.3 Pestaña `Ventas`
**Objetivo:** solo lo vendido (y devuelto en ventas, si hay).

1. Duplica `Sumatorias` y renómbrala `Ventas`.
2. Elimina todo lo que **no** sea ventas: compras, devoluciones en compras, nómina.
3. Deja el título **FACTURAS DE VENTAS** y su fila **TOTAL FACTURAS VENTAS**.
4. Si el cliente tiene notas crédito emitidas, agrégalas en un bloque **DEVOLUCIONES EN VENTAS** con su total.
5. Ajusta el rango del autofiltro y revisa que las fórmulas de total sigan apuntando a las filas correctas (`=P6`, `=SUM(P6:P20)`…).
6. Mantén el encabezado de las filas 1 a 3.

**Columnas de control A y B (`DIAN` / `FISICA`)**
En la fila del título aparecen dos casillas de verificación:

| Columna | Significado |
|---|---|
| A — **DIAN** | La factura fue verificada contra el listado de la DIAN |
| B — **FISICA** | La factura fue verificada contra el soporte físico/digital que entregó el cliente |

- Marca **ambas** cuando el documento aparece en la DIAN **y** el cliente lo tiene.
- Si solo está en una, queda con una sola marca: es una **alerta** (factura que la DIAN reporta pero el cliente no entregó, o factura física que no está en la DIAN).

### 4.4 Pestaña `Compras`
**Objetivo:** todo lo que el cliente compró o gastó. Es la base para la retención.

1. Duplica `Sumatorias` y renómbrala `Compras`.
2. Elimina las ventas.
3. Deja los bloques:
   - **FACTURAS DE COMPRAS** (incluye facturas recibidas, documento soporte y documentos equivalentes como servicios públicos)
   - **DEVOLUCIONES EN COMPRAS** (notas crédito)
   - **NÓMINA**
4. Cada bloque con su fila de total (mismas fórmulas que en `Sumatorias`).
5. Ordena las facturas de **la fecha más reciente a la más antigua** (así quedó en la hoja de referencia) o por proveedor, pero **usa el mismo criterio todos los meses**.
6. Usa las columnas **A (DIAN)** y **B (FISICA)** igual que en `Ventas`.
7. Cuadra: los totales de `Compras` + `Ventas` deben coincidir con los de `Sumatorias`.

### 4.5 Pestaña `Retefuente [Mes]`
**Objetivo:** revisar factura por factura si el cliente **debía practicar retención** y calcularla.

1. Duplica `Compras` y renómbrala, por ejemplo, `Retefuente Octubre`.
2. Agrega a la derecha de la tabla las columnas de trabajo (ver 4.5.1).
3. Revisa **cada factura**, una por una, y asigna el **concepto**.
4. Calcula la base, la tarifa y el valor de la retención.
5. Totaliza por concepto al final.

#### 4.5.1 Columnas sugeridas

| Columna | Contenido |
|---|---|
| Concepto de retención | Compras, servicios, honorarios, arrendamientos, transporte, etc., o **No aplica** |
| Base de retención | Normalmente el **Total Neto** (valor antes de IVA) |
| Base mínima | Mínimo en UVT del concepto (para saber si supera la base) |
| ¿Supera la base? | Sí / No |
| Tarifa | % del concepto |
| Retención | `=SI(supera, base*tarifa, 0)` |
| Observaciones | Régimen del proveedor, autorretenedor, no declarante, etc. |

#### 4.5.2 Criterios para asignar el concepto

Para cada factura pregúntate, en este orden:

1. **¿El cliente es agente de retención?** Las personas naturales solo lo son si cumplen los requisitos legales (p. ej. comerciantes con ingresos o patrimonio superiores al umbral). Si no es agente de retención, la pestaña se llena como **revisión** y la retención es cero.
2. **¿Qué se compró?** Bien, servicio, honorario, arriendo, transporte, servicio público, etc.
3. **¿Quién es el proveedor?** Persona natural o jurídica, régimen, si es **autorretenedor** o **gran contribuyente**, si es **declarante** o **no declarante**.
4. **¿Supera la base mínima?** Cada concepto tiene un mínimo expresado en UVT.
5. **¿Aplica Rete IVA o Rete ICA?** Revisa si el cliente debe practicarlos y las columnas `Rete IVA` y `Rete ICA` que vienen de la DIAN.

> **Tarifas, bases y UVT:** cambian cada año. **Verifica siempre los valores vigentes** (UVT del año y tarifas del Estatuto Tributario y del Decreto Único Reglamentario 1625 de 2016) y no los copies de meses o años anteriores sin revisar. Esta guía **no fija porcentajes** a propósito.

#### 4.5.2.1 Casos que suelen generar dudas
| Documento | Tratamiento sugerido |
|---|---|
| **Servicios públicos** (documento equivalente) | Generalmente **no** se practica retención. |
| **Documento soporte** (compra a no obligado) | Revisa concepto y base: suele tener retención si supera el mínimo. |
| **Notas crédito recibidas** | **Restan** de la base del mes del concepto correspondiente. |
| **Nómina** | Su retención se maneja por **procedimiento de nómina**, no por esta tabla de compras. |
| **Facturas de proveedores autorretenedores** | No se les retiene; deja la observación. |

#### 4.5.3 Resumen final de la pestaña
Al final de la tabla, arma un cuadro por concepto:

| Concepto | Base total | Tarifa | Retención |
|---|---|---|---|
| … | `=SUMAR.SI(...)` | … | `=SUMAR.SI(...)` |
| **TOTAL RETENCIÓN A DECLARAR** | | | `=SUM(...)` |

Ese total es el que va al formulario de retención del mes.

---

## 5. Revisión final (checklist de cierre)

**Descarga**
- [ ] Mes, año y cliente correctos.
- [ ] Archivo guardado en `Cliente / Asuntos Tributarios / Hojas de Trabajo / Mensual / [Año]`.

**Estructura**
- [ ] Pestañas en orden: `Dian`, `Sumatorias`, `Ventas`, `Compras`, `Retefuente [Mes]`.
- [ ] `Dian` sin ninguna modificación.
- [ ] Encabezado (nombre, NIT, "LISTADO DOCUMENTOS ELECTRONICOS DIAN MES AÑO") en las pestañas de trabajo.

**Cuadres**
- [ ] N° de documentos en `Sumatorias` = N° de filas en `Dian`.
- [ ] Total de `Sumatorias` = Total de `Dian`.
- [ ] `Ventas` + `Compras` (+ devoluciones y nómina) = `Sumatorias`.
- [ ] Fórmulas de totales sin errores (`#REF!`, `#VALUE!`).
- [ ] Rangos de `SUM` cubren todas las filas del bloque.

**Verificación documental**
- [ ] Columnas DIAN/FISICA marcadas; pendientes identificados.
- [ ] Facturas con una sola marca listadas para pedirle al cliente o corregir.

**Retefuente**
- [ ] Cada factura con concepto asignado o "No aplica" justificado.
- [ ] Notas crédito aplicadas.
- [ ] Tarifas y UVT del año verificados.
- [ ] Total de retención conciliado con el resumen por concepto.

---

## 6. Errores frecuentes

| Problema | Causa probable | Solución |
|---|---|---|
| El link del correo ya no funciona | Pasó más de 1 hora | Solicitar un nuevo acceso |
| El listado no muestra todo el mes | No se seleccionó del 1 al 31 | Repetir la exportación con el rango completo |
| La exportación no aparece en la tabla inferior | Aún procesa | Esperar y actualizar |
| `Sumatorias` no cuadra con `Dian` | Documento duplicado, omitido o fuera del rango del `SUM` | Filtrar por CUFE y revisar rangos |
| Una venta aparece en compras | Se clasificó solo por tipo y no por Grupo | Revisar columna **Grupo** |
| Documento soporte o nómina contado como venta | Es "Emitido" pero es un costo del cliente | Pasarlo a compras/nómina |
| Autofiltro no incluye las filas nuevas | Rango desactualizado al borrar o insertar filas | Reaplicar el autofiltro |
| Archivo `.xlsm` pierde algo al guardar | Macros o formato | Guardar como `.xlsm` si tiene macros y como `.xlsx` si no las usa |

---

## 7. Resumen en una página

1. DIAN → *Facturando Electrónicamente* → autenticarse → link del correo (1 hora).
2. *Histórico* → *Descarga de listados* → mes/año, día 1 a 31 → *Exportar Excel* → descargar.
3. Drive → Cliente → *Asuntos Tributarios* → *Hojas de Trabajo* → *Mensual* → año → subir.
4. `Dian` (original) → `Sumatorias` (todo agrupado y cuadrado) → `Ventas` → `Compras` (incluye devoluciones, documento soporte y nómina) → `Retefuente [Mes]` (concepto y retención por factura).
5. Cuadrar totales, marcar DIAN/FISICA, verificar tarifas vigentes y cerrar con el checklist.
