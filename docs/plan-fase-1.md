# Plan de la Fase 1 — Núcleo sin interfaz

Objetivo: a partir del listado DIAN, generar `Dian`, `Sumatorias`, `Ventas` y `Compras` con fórmulas
vivas, y verificar los siete cuadres de `AGENTS.md` §5.

Criterio de aceptación:

1. Sobre `Referencias/3-...Oct.2026.xlsm` (89 documentos) el archivo generado coincide en estructura,
   valores y totales (36.190.379,92).
2. Los siete cuadres pasan.
3. No hay `#REF!`, `#VALUE!` ni `#NAME?` después de recalcular.

Sin interfaz, sin retefuente, sin SQLite.

---

## 1. Módulos y firmas

### 1.1 `dominio/enums.py`

```python
class TipoDocumento(StrEnum):
    FACTURA = "FACTURA"
    NOTA_CREDITO = "NOTA_CREDITO"
    DOCUMENTO_SOPORTE = "DOCUMENTO_SOPORTE"
    DOCUMENTO_EQUIVALENTE = "DOCUMENTO_EQUIVALENTE"
    NOMINA = "NOMINA"
    RESPUESTA_DIAN = "RESPUESTA_DIAN"

class Grupo(StrEnum):
    EMITIDO = "EMITIDO"
    RECIBIDO = "RECIBIDO"

class Categoria(StrEnum):
    VENTA = "VENTA"
    COMPRA = "COMPRA"
    DEVOLUCION_COMPRA = "DEVOLUCION_COMPRA"
    DEVOLUCION_VENTA = "DEVOLUCION_VENTA"
    NOMINA = "NOMINA"
    RESPUESTA_DIAN = "RESPUESTA_DIAN"
    SIN_CLASIFICAR = "SIN_CLASIFICAR"
```

`TipoDocumento` guarda el valor normalizado (sin tildes, mayúsculas), no el texto crudo: el texto
crudo se conserva aparte en el documento para escribirlo tal cual en las hojas.

### 1.2 `dominio/modelos.py`

```python
class DocumentoElectronico(BaseModel):
    tipo_texto: str                  # como viene de la DIAN
    tipo: TipoDocumento | None
    cufe: str
    folio: str
    prefijo: str
    divisa: str
    forma_pago: str
    medio_pago: str
    fecha_emision: date
    fecha_recepcion: datetime
    nit_emisor: str
    nombre_emisor: str
    nit_receptor: str
    nombre_receptor: str
    iva: Decimal
    impuestos_otros: Decimal         # ICA + IC + INC + Timbre + ... (todo menos IVA)
    total: Decimal
    estado: str
    grupo: Grupo
    categoria: Categoria
    bloque: Bloque                   # a qué bloque de la hoja va

    @property
    def total_neto(self) -> Decimal:  # total - iva

class Cliente(BaseModel):
    nombre: str
    tipo_identificacion: Literal["NIT", "CC"]
    numero: str                      # sin puntos, como texto
    digito_verificacion: str | None
    @property
    def identificacion_formateada(self) -> str   # "NIT. 901.320.747-4"

class Periodo(BaseModel):
    anio: int
    mes: int
    @property
    def primer_dia / ultimo_dia -> date
    @property
    def titulo(self) -> str          # "LISTADO DOCUMENTOS ELECTRONICOS DIAN OCTUBRE 2026"
    @property
    def mes_abrev(self) -> str       # "Oct"
    def nombre_archivo(self, cliente: Cliente) -> str

class Bloque(StrEnum):
    FACTURAS_VENTAS / DEVOLUCIONES_VENTAS / FACTURAS_COMPRAS / DEVOLUCIONES_COMPRAS / NOMINA

class ResultadoMes(BaseModel):
    documentos: tuple[DocumentoElectronico, ...]
    bloques: dict[Bloque, tuple[DocumentoElectronico, ...]]
    excluidos: tuple[DocumentoElectronico, ...]     # Application response, etc.
    total: Decimal
    iva: Decimal
    total_neto: Decimal
```

Dinero en `Decimal`, nunca `float`, hasta el momento de escribir la celda.

### 1.3 `reglas/clasificador.py`

```python
def normalizar(texto: str) -> str:
    """minúsculas, sin tildes, espacios colapsados y recortados."""

def clasificar(tipo_texto: str, grupo_texto: str) -> tuple[TipoDocumento | None, Categoria]:
    """Nunca lanza. Lo que no reconoce devuelve (None, SIN_CLASIFICAR)."""

def bloque_de(categoria: Categoria) -> Bloque | None
```

Tabla declarativa (tuplas de prefijo normalizado, grupo → categoría):

| prefijo normalizado | emitido | recibido |
|---|---|---|
| `factura electronica` | `VENTA` | `COMPRA` |
| `nota de credito electronica` | `DEVOLUCION_VENTA` | `DEVOLUCION_COMPRA` |
| `documento soporte` | `COMPRA` | `COMPRA` (D-10) |
| `documento equivalente` | `SIN_CLASIFICAR` | `COMPRA` |
| `nomina individual` | `NOMINA` | `SIN_CLASIFICAR` |
| `application response` | `RESPUESTA_DIAN` | `RESPUESTA_DIAN` (D-08) |
| cualquier otra cosa | `SIN_CLASIFICAR` | `SIN_CLASIFICAR` |

Coincidencia por **prefijo** para tolerar sufijos reales como
`Documento equivalente - Servicios públicos domiciliarios`.

### 1.4 `dominio/cuadres.py`

```python
@dataclass(frozen=True)
class ResultadoCuadre:
    codigo: str            # "C1".."C7"
    titulo: str
    ok: bool
    detalle: str
    bloqueante: bool = True

def ejecutar_cuadres(resultado, cliente, periodo, *, total_dian, filas_dian,
                     impuestos_otros_dian) -> tuple[ResultadoCuadre, ...]
```

| Código | Verificación |
|---|---|
| C1 | `filas de Sumatorias + excluidos justificados = filas de Dian` |
| C2 | suma de bloques = suma de `Total` de `Dian` (tolerancia 0,01 por redondeo) |
| C3 | ningún CUFE se repite entre bloques |
| C4 | `Ventas + Compras + Devoluciones + Nómina = Sumatorias` |
| C5 | todas las fechas de emisión dentro del periodo |
| C6 | la identificación del cliente aparece como emisor o receptor |
| C7 | impuestos distintos de IVA en cero (D-19) |

C7 es un cuadre nuevo, no está en `AGENTS.md` §5, pero evita el neto silenciosamente incorrecto.
Los siete devuelven `ok=False` con detalle accionable, nunca lanzan.

### 1.5 `puertos.py`

```python
class LectorListado(Protocol):
    def leer(self, ruta: Path) -> ListadoDian: ...

class EscritorHoja(Protocol):
    def escribir(self, resultado, cliente, periodo, destino: Path, *,
                 ruta_listado: Path) -> Path: ...
```

`ListadoDian` (en `dominio/modelos.py`): `documentos`, `total`, `iva`, `filas`.

### 1.6 `infraestructura/lector_dian_xlsx.py`

```python
COLUMNAS_ESPERADAS: tuple[str, ...]        # las 32 de la sección 3

class ErrorListado(ValueError): ...

class LectorDianXlsx:
    def leer(self, ruta: Path) -> ListadoDian
```

Responsabilidades:

- Abrir con `openpyxl` (`data_only=True`), validar que exista una hoja con las 32 columnas en orden.
- Leer todo como texto (`str`), preservando ceros y letras en NIT y folio.
- Parsear `Fecha Emisión` con `strptime("%d-%m-%Y")` y `Fecha Recepción` con `fromisoformat`.
- Convertir a `Decimal` los valores monetarios con `Decimal(str(valor))`.
- Lanzar `ErrorListado` con el número de fila y la columna exacta ante cualquier anomalía.
- No clasificar: eso es del clasificador.

### 1.7 `infraestructura/estilos.py`

Constantes de D-16: fuentes, rellenos, formatos monetarios, anchos y alturas, en un solo lugar.

### 1.8 `infraestructura/escritor_xlsx.py`

```python
class EscritorOpenpyxl:
    def escribir(self, resultado, cliente, periodo, destino, *, ruta_listado) -> Path
```

- Hoja `Dian`: se copia del libro de origen celda por celda (valor, estilo, ancho, alto) sin tocar
  nada, y se conserva `freeze_panes` y el autofiltro.
- `Sumatorias`, `Ventas`, `Compras`: se construyen con tres helpers privados
  (`_encabezado`, `_bloque`, `_total`) que reciben la fila de inicio y devuelven la siguiente.
- Fórmulas: `Total Neto =R{f}-P{f}`, totales `=SUM(P{ini}:P{fin})`, en inglés (D-03).
- Autofiltro y `freeze_panes` al final, cuando ya se conocen las filas.
- Nunca escribe valores calculados en Python en las celdas de total.

### 1.9 `aplicacion/procesar_mes.py`

```python
@dataclass(frozen=True)
class ResultadoProcesamiento:
    resultado: ResultadoMes
    cuadres: tuple[ResultadoCuadre, ...]
    ruta_listado: Path
    @property
    def puede_exportar(self) -> bool     # ningún cuadre bloqueante falla

def procesar_mes(ruta_listado: Path, cliente: Cliente, periodo: Periodo,
                 lector: LectorListado) -> ResultadoProcesamiento
```

### 1.10 `aplicacion/exportar_hoja.py`

```python
class CuadreFallido(RuntimeError): ...

def exportar_hoja(proceso: ResultadoProcesamiento, cliente: Cliente, periodo: Periodo,
                  carpeta: Path, escritor: EscritorHoja) -> Path
```

Bloquea la escritura si `puede_exportar` es falso y devuelve el detalle de los cuadres fallidos.

---

## 2. Pruebas a escribir (en este orden)

### Unitarias

| Archivo | Qué cubre |
|---|---|
| `test_clasificador.py` | las 7 combinaciones de la tabla; `Application response`; documento equivalente con sufijo; nómina recibida; tipo y grupo desconocidos; tildes, mayúsculas y espacios múltiples; nunca lanza |
| `test_modelos.py` | `total_neto`, `Periodo.titulo` / `mes_abrev` / `nombre_archivo`, `Cliente.identificacion_formateada` con y sin dígito de verificación, CC en vez de NIT |
| `test_cuadres.py` | cada cuadre en verde y en rojo; CUFE duplicado; documento fuera del mes; cliente ausente; impuestos ≠ 0; tolerancia de redondeo |
| `test_lector.py` | encabezados correctos; columna faltante o fuera de orden; fecha inválida; NIT con ceros; folio con letras; celda numérica donde debe haber texto; archivo sin filas |

### Integración

| Archivo | Qué cubre |
|---|---|
| `test_escritor.py` | sobre 5 documentos sintéticos: merges `E1:S1`, encabezados, `freeze A5`, autofiltro, `freeze A2` en `Dian`, fórmulas `=R-P` y `SUM` con el rango correcto, bloques vacíos omitidos, columnas A/B presentes en Ventas y Compras |
| `test_integracion_hoja.py` | golden contra `tests/fixtures/` (sintético, versionado) y `@pytest.mark.referencias` contra `Referencias/3-...Oct.2026.xlsm` comparando lo definido en D-14 |
| `test_recalculo.py` | con `soffice` disponible: recalcular y verificar que no aparezcan errores de fórmula; se salta si no está instalado |

### Fixture sintético

Script `tests/herramientas/generar_listado_sintetico.py` que produce
`tests/fixtures/listado_dian_sintetico.xlsx` con datos inventados:

- 2 facturas emitidas, 6 recibidas, 1 documento soporte, 1 documento equivalente, 1 nota crédito
  recibida, 1 nota crédito emitida, 1 nómina, 1 `Application response`.
- Folio `NCP14858`, prefijo vacío, NIT con ceros a la izquierda, CUFE repetido en una fila extra
  para probar C3, y una fecha del mes anterior para probar C5.

Se genera una vez y se versiona el `.xlsx`, para que las pruebas no dependan de datos reales.

---

## 3. Orden de implementación

1. Fixture sintético y `test_lector.py` en rojo.
2. `enums`, `modelos`, `clasificador` + `test_clasificador.py` y `test_modelos.py`.
3. `cuadres` + `test_cuadres.py`.
4. `LectorDianXlsx` + `test_lector.py` en verde.
5. `estilos` y `EscritorOpenpyxl` con `test_escritor.py`.
6. `procesar_mes` y `exportar_hoja`.
7. `test_integracion_hoja.py` contra la referencia real, ajuste fino de estilos y de etiquetas.
8. Recalculo con LibreOffice y commit de cierre.

Cada paso con su commit. Al final: resumen, cuadres en verde y espera de aprobación para la Fase 2.

---

## 4. Riesgos y supuestos

| Riesgo | Mitigación |
|---|---|
| El listado real trae tipos de documento nuevos | `SIN_CLASIFICAR` visible y reportado; nunca se descarta |
| El `Dian` de origen tiene formato raro (filas 1000, estilos) | se copia celda a celda, sin reinterpretar |
| Redondeos de 1 centavo | comparación con tolerancia de 0,01 solo en C2 |
| `Application response` (D-08) ya decidido | categoría `RESPUESTA_DIAN`, excluida de las hojas y contada en C1 como excluido justificado |
| La hoja de referencia tiene errores propios (D-04, D-13) | el golden normaliza; no se copian los errores |
