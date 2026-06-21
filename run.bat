@echo off
REM Arranca el microservicio. Ejecutar despues de setup_windows.bat
call .venv\Scripts\activate.bat
echo Servicio en  http://127.0.0.1:8000   (Ctrl+C para detener)
echo Docs interactivas:  http://127.0.0.1:8000/docs
uvicorn simulador_service:app --host 127.0.0.1 --port 8000
