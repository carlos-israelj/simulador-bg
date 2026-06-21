#!/bin/bash

# Script de inicio para Render

# Instalar dependencias del sistema para Playwright (si no están)
playwright install-deps chromium 2>/dev/null || true

# Iniciar el servidor
uvicorn simulador_service:app --host 0.0.0.0 --port ${PORT:-8000}
