# dian_hojas

Aplicación de escritorio para preparar la **hoja de trabajo mensual de retención en la fuente**
a partir del listado de documentos electrónicos descargado de la DIAN.

Entrada: el Excel que exporta la DIAN.
Salida: `Dian` | `Sumatorias` | `Ventas` | `Compras` | `Retefuente [Mes]`.

El contexto completo, las reglas y el plan por fases están en [`AGENTS.md`](AGENTS.md).
Las decisiones abiertas y las ya tomadas están en [`DECISIONES.md`](DECISIONES.md).

## Estado

Fase 0 (preparación). Todavía no hay lógica de negocio.

## Entorno

```powershell
uv venv --python 3.12
uv pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest
```

## Estructura

```
src/dian_hojas/
├── dominio/          # Python puro: modelos, enums, cuadres
├── reglas/           # clasificador y motor de retefuente
├── aplicacion/       # casos de uso
├── puertos.py        # Protocol: lector, escritor, repositorio
├── infraestructura/  # openpyxl, pandas, sqlite, yaml
└── interfaz/         # PySide6 (vistas + viewmodels)
reglas/               # YAML por año (UVT, bases, tarifas) — los provee el usuario
tests/fixtures/       # solo archivos anonimizados o sintéticos
Referencias/          # archivos reales del usuario — fuera de git
```
