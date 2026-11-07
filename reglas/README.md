# reglas/

Tablas tributarias por año, en YAML. **Las provee el usuario**; el código no inventa ni completa
valores (regla 4 de `AGENTS.md`).

Puedes editar el archivo a mano o desde la interfaz de la aplicación:
**«Configuración tributaria…» → UVT, base mínima (UVT) y tarifa por concepto → Guardar**.
El mismo diálogo tiene **«Cargar YAML existente…»** si ya tienes el archivo.

Estructura prevista de `reglas/2026.yaml`:

```yaml
anio: 2026
uvt_pesos: <pendiente>
conceptos:
  compras:
    base_minima_uvt: <pendiente>
    tarifa: <pendiente>
  servicios:
    base_minima_uvt: <pendiente>
    tarifa: <pendiente>
  honorarios:
    base_minima_uvt: <pendiente>
    tarifa: <pendiente>
  arrendamientos:
    base_minima_uvt: <pendiente>
    tarifa: <pendiente>
  transporte:
    base_minima_uvt: <pendiente>
    tarifa: <pendiente>
```

Si falta una clave, la aplicación debe fallar con un mensaje que diga exactamente cuál falta.

Al empaquetar la aplicación, esta carpeta se copia **al lado del `.exe`** (no dentro del binario),
para que siga siendo editable. Ver `docs/empaquetado.md`.
