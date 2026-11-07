# Construye el ejecutable de Windows y deja las reglas al lado.
# Uso (desde la raíz del repositorio o desde cualquier carpeta):
#   powershell -ExecutionPolicy Bypass -File scripts\construir_exe.ps1
$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

$python = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "No existe .venv. Crea el entorno e instala las dependencias antes de empaquetar."
}

& $python -m pip install --upgrade ".[gui,empaquetado]"
& $python -m PyInstaller "dian_hojas.spec" --noconfirm

$destino = Join-Path $raiz "dist\HojasTrabajoDIAN"
if (Test-Path (Join-Path $destino "reglas")) {
    Remove-Item (Join-Path $destino "reglas") -Recurse -Force
}
Copy-Item (Join-Path $raiz "reglas") (Join-Path $destino "reglas") -Recurse -Force

Write-Host ""
Write-Host "Listo: $destino\HojasTrabajoDIAN.exe"
Write-Host "Las reglas quedaron en: $destino\reglas"
Write-Host "Si usas OCR, instala el extra [ocr] antes de empaquetar y el motor Tesseract en Windows."
