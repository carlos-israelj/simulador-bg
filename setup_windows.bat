@echo off
REM ============================================================
REM  Setup del microservicio Simulador BG  (Windows)
REM  Crea el entorno virtual, instala dependencias y el navegador.
REM  Ejecutar UNA sola vez, parado en la carpeta del proyecto:
REM      setup_windows.bat
REM ============================================================

echo.
echo [1/4] Creando entorno virtual .venv ...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: no se pudo crear el venv. Verifica que Python este instalado y en el PATH.
    exit /b 1
)

echo.
echo [2/4] Activando entorno e actualizando pip ...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo [3/4] Instalando dependencias de requirements.txt ...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: fallo la instalacion de dependencias.
    exit /b 1
)

echo.
echo [4/4] Descargando navegador Chromium para Playwright ...
playwright install chromium
if errorlevel 1 (
    echo ERROR: fallo la descarga de Chromium.
    exit /b 1
)

echo.
echo ============================================================
echo  LISTO. Para arrancar el servicio:
echo      call .venv\Scripts\activate.bat
echo      uvicorn simulador_service:app --host 127.0.0.1 --port 8000
echo ============================================================
