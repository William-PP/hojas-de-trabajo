# tests/fixtures/

Solo archivos **sintéticos** o **anonimizados** (regla 10 de `AGENTS.md`).

- `listado_dian_sintetico.xlsx`: fabricado a mano, cubre las siete combinaciones tipo/grupo y los
  casos borde (folio con letras, prefijo vacío, NIT con ceros, CUFE repetido, etc.). Todavía no existe.
- `hoja_esperada_sintetica.xlsx`: salida esperada para ese listado. Todavía no existe.

Los archivos reales del usuario viven en `Referencias/`, fuera de git, y las pruebas que los usan
están marcadas con `@pytest.mark.referencias`.
