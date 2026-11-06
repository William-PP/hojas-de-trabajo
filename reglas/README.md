# reglas/

Tablas tributarias por año, en YAML. **Las provee el usuario**; el código no inventa ni completa
valores (regla 4 de `AGENTS.md`).

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
