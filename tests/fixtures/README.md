# tests/fixtures/

Solo archivos **sintéticos** o **anonimizados** (regla 10 de `AGENTS.md`).

- No hay un `.xlsx` versionado. El listado sintético se genera **en memoria** con
  `tests/herramientas/listado_sintetico.py:crear_listado` y se escribe en una carpeta temporal
  durante las pruebas (decisión D-25).
- Cubre las siete combinaciones tipo/grupo y los casos borde (folio con letras, prefijo vacío, NIT
  con ceros, CUFE repetido, documento desconocido, impuestos distintos de IVA, fecha fuera de
  periodo, mes vacío).
- La salida esperada se compara en memoria, no como binario: ver `test_escritor.py`.
- Los archivos reales del usuario viven en `Referencias/`, fuera de git, y las pruebas que los usan
  están marcadas con `@pytest.mark.referencias`.
