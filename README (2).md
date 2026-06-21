# Microservicio Simulador BG

Expone el Simulador de Multicrédito de Banco Guayaquil como endpoint HTTP local
para que Power Automate lo consuma, sin automatizar la UI desde el flujo.

## Archivos

- `simulador_service.py` — el servicio (FastAPI + Playwright)
- `requirements.txt` — dependencias con versiones fijadas
- `setup_windows.bat` / `setup.sh` — instalación de una pasada
- `run.bat` — arranque rápido (Windows)

## Instalación

Pon todos los archivos en una carpeta y, parado ahí:

### Windows
```bat
setup_windows.bat
```

### macOS / Linux
```bash
bash setup.sh
```

### Manual (cualquier SO)
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# mac/lin:  source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

> `playwright install chromium` descarga el navegador (~150 MB) desde el CDN de
> Playwright. Necesita internet la primera vez.

## Arrancar

```bash
uvicorn simulador_service:app --host 127.0.0.1 --port 8000
```
(En Windows también: `run.bat`)

- Servicio: http://127.0.0.1:8000
- Docs interactivas (probar a mano): http://127.0.0.1:8000/docs
- Salud: http://127.0.0.1:8000/health

## Probar

```bash
curl -X POST http://127.0.0.1:8000/simular ^
  -H "Content-Type: application/json" ^
  -d "{\"monto\":10000,\"meses\":24,\"amortizacion\":\"aleman\",\"correo\":\"gcalero@binaria.com.ec\"}"
```
(en Windows usa `^` para saltos de línea; en bash usa `\`)

## Conectar con Power Automate

- **Power Automate Desktop**: corre en tu máquina, alcanza `127.0.0.1:8000`
  directo. Usa la acción de invocar servicio web / HTTP apuntando al endpoint.
- **Flujo de nube (cloud)**: NO ve `localhost`. Necesitas un *on-premises data
  gateway*, o expón el servicio en una IP/host accesible.

Acción HTTP → `POST http://127.0.0.1:8000/simular`, body JSON con
`monto`, `meses`, `amortizacion`, `correo`. Luego **Parse JSON** sobre la
respuesta para usar `cuota_mensual`, `capital`, `total_pagar`, `tabla_amortizacion`, etc.

## Pendiente de calibrar

Los selectores marcados `(TODO VERIFICAR)` en `simulador_service.py` deben
confirmarse contra la página real. Lo más fiable:

```bash
playwright codegen https://www.bancoguayaquil.com/creditos/simuladores/
```

Llena el formulario y copia los selectores que genere.
