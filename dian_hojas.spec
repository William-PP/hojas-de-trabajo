# -*- mode: python ; coding: utf-8 -*-

"""Empaquetado de la aplicación con PyInstaller (Windows 10/11).

    .venv\\Scripts\\python.exe -m PyInstaller dian_hojas.spec --noconfirm

La carpeta `reglas/` **no** se incluye dentro del binario: se copia al lado del `.exe` para que el
usuario pueda editarla (ver `docs/empaquetado.md`). El OCR es opcional; solo se incluyen sus
módulos si están instalados al construir. El antivirus puede marcar falsos positivos por los
empaquetadores de PyInstaller; eso no significa que el `.exe` tenga virus (ver README).
"""

from importlib.util import find_spec
from pathlib import Path

raiz = Path(SPECPATH)
ocultos = [modulo for modulo in ("pytesseract", "pdf2image") if find_spec(modulo)]

a = Analysis(
    [str(raiz / "src" / "dian_hojas" / "__main__.py")],
    pathex=[str(raiz / "src")],
    binaries=[],
    datas=[],
    hiddenimports=ocultos,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HojasTrabajoDIAN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="HojasTrabajoDIAN",
)
