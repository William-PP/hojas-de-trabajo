# Empaquetado como aplicación de Windows (`.exe`)

La aplicación se empaqueta con **PyInstaller** en modo carpeta (`onedir`). El `.exe` queda en:

```
dist\HojasTrabajoDIAN\HojasTrabajoDIAN.exe
```

## 1. Construir

Desde la raíz del repositorio, con el entorno virtual creado:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\construir_exe.ps1
```

El script:

1. instala el proyecto con los extras `gui` y `empaquetado`;
2. ejecuta `PyInstaller dian_hojas.spec --noconfirm`;
3. copia `reglas\` dentro de `dist\HojasTrabajoDIAN\reglas`.

También se puede hacer a mano:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[gui,empaquetado]"
.venv\Scripts\python.exe -m PyInstaller dian_hojas.spec --noconfirm
```

## 2. Dónde viven las reglas tributarias

**No** van dentro del `.exe`. La aplicación las busca así:

1. si existe la variable de entorno `DIAN_HOJAS_REGLAS`, usa esa carpeta;
2. si está empaquetada, usa `reglas\` al lado del `.exe`;
3. en el repositorio, usa `reglas\` en la raíz.

Por eso el usuario puede editar `reglas\2026.yaml` con el editor de la interfaz
(«Configuración tributaria…») o cargar el YAML que le entregue su contador. Al actualizar el
programa, basta con conservar esa carpeta.

Los datos locales (perfiles de clientes y decisiones de retención) se guardan en
`%USERPROFILE%\.dian_hojas\retefuente.sqlite`. Se puede cambiar con `DIAN_HOJAS_DATOS`.

## 3. OCR opcional

El OCR **no es obligatorio**: la aplicación funciona sin él. Solo se usa si el usuario pulsa
«Verificar soportes (OCR, opcional)…».

Para habilitarlo en el entorno de desarrollo:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[gui,ocr]"
```

Además hacen falta los programas del sistema:

- **Tesseract OCR** (por ejemplo, el instalador de UB Mannheim para Windows);
- **poppler** si se van a leer PDF (o entregar los soportes como imágenes PNG/JPG).

Si faltan, la interfaz muestra un aviso claro y sigue trabajando; no bloquea la exportación.

## 4. Qué no se versiona

`build\`, `dist\` y `*.spec` generados quedan en `.gitignore` (el `.spec` del proyecto sí se
versiona a propósito). Nunca se copian datos reales de clientes al repositorio.
