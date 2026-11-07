# dian_hojas

Aplicación de escritorio para preparar la **hoja de trabajo mensual de retención en la fuente**
a partir del listado de documentos electrónicos descargado de la DIAN.

Entrada: el Excel que exporta la DIAN.
Salida: `Dian` | `Sumatorias` | `Ventas` | `Compras` | `Retefuente [Mes]`.

El contexto completo, las reglas y el plan por fases están en [`AGENTS.md`](AGENTS.md).
Las decisiones de diseño están en [`DECISIONES.md`](DECISIONES.md).
El plan y cierre de la última fase están en [`docs/plan-fase-4.md`](docs/plan-fase-4.md).

## Estado

Fases 0 a 4 implementadas: núcleo, interfaz, retención, perfiles por cliente, editor de reglas
tributarias, soportes físicos opcionales y empaquetado `.exe`.

Pendiente: el YAML tributario real de 2026 (lo provee el usuario) y probar el `.exe` en una máquina
limpia.

## Entorno

```powershell
uv venv --python 3.12
uv pip install -e ".[dev-gui]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m dian_hojas
```

`dev-gui` incluye PySide6 y pytest-qt. Sin PySide6 las pruebas de interfaz se saltan.

## Configuración tributaria

Las UVT, bases mínimas y tarifas salen **solo** de `reglas/[año].yaml`. Se pueden editar a mano o
desde la aplicación con **«Configuración tributaria…»**; el mismo diálogo permite **cargar un YAML
existente**. La aplicación no inventa ni completa valores.

## OCR opcional

La aplicación funciona sin OCR. Para leer soportes en PDF o imagen:

```powershell
uv pip install -e ".[gui,ocr]"
```

Además hay que instalar Tesseract y, para PDF, poppler. Si faltan, la interfaz avisa y sigue.

## Empaquetado

```powershell
powershell -ExecutionPolicy Bypass -File scripts\construir_exe.ps1
```

El detalle está en [`docs/empaquetado.md`](docs/empaquetado.md). La carpeta `reglas/` queda al lado
del ejecutable para que siga siendo editable.

## Estructura

```
src/dian_hojas/
├── dominio/          # Python puro: modelos, enums, cuadres, soportes
├── reglas/           # clasificador, motor de retefuente y configuración YAML
├── aplicacion/       # casos de uso
├── puertos.py        # Protocol: lector, escritor, repositorio, OCR
├── infraestructura/  # openpyxl, pandas, sqlite, yaml, OCR
├── interfaz/         # PySide6 (vistas + viewmodels)
└── rutas.py          # reglas y datos locales (fuente y .exe)
reglas/               # YAML por año (UVT, bases, tarifas) — los provee el usuario
tests/fixtures/       # solo archivos anonimizados o sintéticos
Referencias/          # archivos reales del usuario — fuera de git
```
