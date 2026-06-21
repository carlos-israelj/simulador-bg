#!/usr/bin/env bash
# ============================================================
#  Setup del microservicio Simulador BG  (macOS / Linux)
#  Uso:  bash setup.sh
# ============================================================
set -e

echo "[1/4] Creando entorno virtual .venv ..."
python3 -m venv .venv

echo "[2/4] Activando e actualizando pip ..."
source .venv/bin/activate
python -m pip install --upgrade pip

echo "[3/4] Instalando dependencias ..."
pip install -r requirements.txt

echo "[4/4] Descargando Chromium ..."
playwright install chromium

echo ""
echo "============================================================"
echo " LISTO. Para arrancar:"
echo "   source .venv/bin/activate"
echo "   uvicorn simulador_service:app --host 127.0.0.1 --port 8000"
echo "============================================================"
