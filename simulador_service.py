"""
Microservicio local: expone el Simulador de Multicredito de Banco Guayaquil
como un endpoint HTTP que Power Automate puede consumir.

Patron: "scraper como servicio".
    Power Automate --POST /simular--> este servicio --headless--> simulador BG
    el servicio devuelve JSON limpio con cuota, detalle y tabla de amortizacion.

Por que asi: la funcion de calculo del banco vive dentro de un closure de modulo
minificado (no esta en window), por lo que no se puede invocar directa. La via
robusta es manejar el DOM en headless y leer el resultado que el propio banco calcula.

Requisitos:
    pip install fastapi uvicorn playwright
    playwright install chromium

Ejecutar:
    uvicorn simulador_service:app --host 127.0.0.1 --port 8000

IMPORTANTE - selectores: los marcados con (TODO VERIFICAR) hay que confirmarlos
contra la pagina real. La forma mas rapida y fiable de obtenerlos es grabar la
interaccion con el codegen de Playwright (no adivinar a mano):

    playwright codegen https://www.bancoguayaquil.com/creditos/simuladores/

Eso abre el navegador y va escribiendo el codigo con los selectores exactos
mientras llenas el formulario. Pega aqui los que te genere.
"""

from contextlib import asynccontextmanager
import random
import asyncio
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

URL = "https://www.bancoguayaquil.com/creditos/simuladores/"

# Configuración de entorno (producción vs desarrollo)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # production o development
HEADLESS_MODE = os.getenv("HEADLESS", "true" if ENVIRONMENT == "production" else "false").lower() == "true"

# Configuración de proxy (opcional, se puede configurar via variables de entorno)
# Formato: http://username:password@proxy-server:port o http://proxy-server:port
PROXY_SERVER = os.getenv("PROXY_SERVER")  # ej: "http://proxy.ejemplo.com:8080"
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

# Estado compartido: un solo navegador para todas las peticiones (mas rapido).
_state = {}
# Almacenamiento simple de resultados (última simulación)
_ultimo_resultado = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    pw = await async_playwright().start()
    # headless se configura automáticamente según ENVIRONMENT
    # - development (local): headless=False para debugging
    # - production (Render/cloud): headless=True
    browser = await pw.chromium.launch(
        headless=HEADLESS_MODE,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--window-size=1920,1080",
            "--disable-gpu"  # Importante para servidores sin GPU
        ]
    )
    _state["pw"] = pw
    _state["browser"] = browser
    yield
    await browser.close()
    await pw.stop()


app = FastAPI(lifespan=lifespan, title="Simulador BG")


class SimulacionInput(BaseModel):
    monto: float = Field(..., ge=2000, le=50000)      # monto minimo: $2.000, maximo estimado: $50.000
    meses: int = Field(..., ge=12, le=60)             # limites reales: 12-60, paso 12
    amortizacion: str = Field(..., pattern="(?i)^(aleman|frances)$")
    correo: str | None = None                          # se usa aguas abajo, no en el calculo


def _solo_meses_validos(m: int) -> int:
    """El portal solo permite 12, 24, 36, 48, 60. Redondea al permitido mas cercano."""
    permitidos = [12, 24, 36, 48, 60]
    return min(permitidos, key=lambda x: abs(x - m))


@app.post("/simular")
async def simular(data: SimulacionInput):
    browser = _state["browser"]

    # Configurar proxy si está disponible
    context_options = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "es-EC",
        "timezone_id": "America/Guayaquil",
        "java_script_enabled": True
    }

    # Agregar proxy si está configurado
    if PROXY_SERVER:
        proxy_config = {"server": PROXY_SERVER}
        if PROXY_USERNAME and PROXY_PASSWORD:
            proxy_config["username"] = PROXY_USERNAME
            proxy_config["password"] = PROXY_PASSWORD
        context_options["proxy"] = proxy_config

    # Crear contexto con user-agent realista y configuraciones anti-detección
    context = await browser.new_context(**context_options)

    # Inyectar scripts anti-detección antes de navegar
    await context.add_init_script("""
        // Ocultar webdriver
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

        // Sobrescribir propiedades de detección
        window.navigator.chrome = {runtime: {}};

        // Permisos de notificaciones (comportamiento de navegador real)
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({state: 'denied'})
            })
        });

        // Plugins (comportamiento de navegador real)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-EC', 'es', 'en']
        });
    """)

    page = await context.new_page()
    try:
        # Timeout aumentado a 60 segundos para manejar captchas y validaciones
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # Delay inicial MUY largo para dar tiempo a que la página cargue completamente
        await asyncio.sleep(random.uniform(5.0, 8.0))

        # Cerrar popup de cookies si aparece
        try:
            aceptar_cookies = page.get_by_role("button", name="Aceptar")
            await aceptar_cookies.click(timeout=5000)
            await asyncio.sleep(random.uniform(0.5, 1.0))
        except:
            pass  # Si no hay popup, continuar

        # Esperar a que el formulario del simulador esté visible
        await page.wait_for_selector("input.multicredito__input", timeout=60000)

        # NO hacer scroll manual - dejar que scroll_into_view_if_needed lo maneje
        # cuando interactuemos con los elementos
        await asyncio.sleep(random.uniform(1.5, 2.5))  # Delay antes de interactuar

        # 1) Monto del credito (input de texto con placeholder $0.00).
        # Formatear monto sin comas (el campo acepta números simples)
        await asyncio.sleep(random.uniform(1.5, 3.0))  # Delay humano largo
        monto_input = page.locator("input.multicredito__input").first
        await monto_input.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.5, 1.0))  # Pausa antes de escribir
        # Limpiar el campo primero y luego llenar
        await monto_input.clear()
        await asyncio.sleep(0.3)
        # Escribir el monto como número entero sin formato
        await monto_input.fill(str(int(data.monto)))

        # 2) Plazo: es un <input type=range> id=meses. Los sliders se setean por
        #    JS + disparo manual de eventos input/change para que React reaccione.
        await asyncio.sleep(random.uniform(1.0, 2.0))  # Delay humano largo
        meses = _solo_meses_validos(data.meses)
        await page.eval_on_selector(
            "#meses",
            """(el, v) => {
                el.value = v;
                el.dispatchEvent(new Event('input',  {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }""",
            str(meses),
        )

        # 3) Tipo de amortizacion (boton Aleman / Frances).
        await asyncio.sleep(random.uniform(1.5, 2.5))  # Delay humano largo
        etiqueta = "Alemán" if data.amortizacion.lower().startswith("alem") else "Francés"
        boton_tipo = page.get_by_role("button", name=etiqueta, exact=True)
        await boton_tipo.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.5, 1.0))  # Pausa antes de click
        await boton_tipo.click()

        # 4) Calcular.
        await asyncio.sleep(random.uniform(2.0, 3.5))  # Delay humano largo antes de calcular
        boton_calcular = page.locator("button.multicredito__buttonCalcular")
        await boton_calcular.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.5, 1.0))  # Pausa antes de click

        # Screenshot antes de calcular
        await page.screenshot(path="debug_before_calculate.png")

        await boton_calcular.click()

        # Esperar procesamiento
        await asyncio.sleep(random.uniform(3.0, 5.0))

        # Screenshot después de calcular
        await page.screenshot(path="debug_after_calculate.png")

        # Esperar a que aparezcan los resultados - buscar por el texto "Cuotas mensuales"
        await page.wait_for_selector("text=Cuotas mensuales", timeout=45000)
        await asyncio.sleep(random.uniform(3.0, 5.0))  # Esperar render completo

        # Hacer scroll a los resultados
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # 5) Leer el detalle del credito.
        #    Helper: dado el texto de una etiqueta, devuelve el monto de su fila.
        async def valor(etiqueta_texto: str) -> str:
            loc = page.locator(f"text={etiqueta_texto}").first
            fila = loc.locator("xpath=ancestor::*[1]")
            txt = await fila.inner_text()
            return txt.replace(etiqueta_texto, "").strip()

        # Obtener la cuota mensual (el número grande que está después de "Cuotas mensuales")
        cuota_section = page.locator("text=Cuotas mensuales").locator("xpath=following-sibling::*[1]")
        cuota_mensual = await cuota_section.inner_text()

        resultado = {
            "monto": data.monto,
            "meses": meses,
            "amortizacion": etiqueta,
            "correo": data.correo,
            "cuota_mensual": cuota_mensual.strip(),
            "capital":        await valor("Capital:"),
            "impuesto_solca": await valor("Impuesto de Solca:"),
            "total_interes":  await valor("Total de interés:"),
            "total_seguros":  await valor("Total de seguros:"),
            "total_pagar":    await valor("Total a pagar:"),
        }

        # 6) Tabla de amortizacion: abrir el modal y leer filas.
        await page.get_by_text("Ver tabla de amortización").click()
        await page.wait_for_timeout(1000)

        filas = []
        for tr in await page.locator("table tr").all():
            texto = await tr.inner_text()
            celdas = [c.strip() for c in texto.split("\t") if c.strip()]
            # las filas de datos empiezan con el numero de cuota
            if celdas and celdas[0].isdigit():
                filas.append({
                    "n": celdas[0],
                    "saldo": celdas[1] if len(celdas) > 1 else None,
                    "capital": celdas[2] if len(celdas) > 2 else None,
                    "interes": celdas[3] if len(celdas) > 3 else None,
                    "s_desgravamen": celdas[4] if len(celdas) > 4 else None,
                    "s_cesantia": celdas[5] if len(celdas) > 5 else None,
                    "total_seguros": celdas[6] if len(celdas) > 6 else None,
                    "cuota": celdas[7] if len(celdas) > 7 else None,
                })
        resultado["tabla_amortizacion"] = filas

        # Guardar resultado para el endpoint GET
        global _ultimo_resultado
        _ultimo_resultado = resultado

        return resultado

    except Exception as e:
        # 502 = el upstream (el simulador) fallo. Power Automate puede reintentar.
        raise HTTPException(status_code=502, detail=f"Error en simulacion: {e}")
    finally:
        await context.close()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/resultado")
async def obtener_resultado():
    """
    Obtiene los datos del último cálculo realizado:
    - Monto de Cuotas Mensuales
    - Detalle del crédito:
      · Capital
      · Impuesto de Solca
      · Total de interés
      · Total de seguros
      · Total a pagar
    """
    if _ultimo_resultado is None:
        raise HTTPException(
            status_code=404,
            detail="No hay resultados disponibles. Ejecuta POST /simular primero."
        )
    return _ultimo_resultado


# -----------------------------------------------------------------------------
# NOTAS
#
# Anti-bot: el sitio carga una capa de deteccion (eudaapi + beacons). Si en
# headless ves resultados vacios o bloqueos, prueba headless=False, o agrega un
# user-agent realista en new_context(user_agent=...). No abuses de la frecuencia
# de llamadas.
#
# Descarga del PDF (paso 5 del ejercicio): el boton "Descargar Tabla" se puede
# capturar con page.expect_download(). Se puede agregar otro endpoint /pdf que
# guarde el archivo y devuelva la ruta. Pide ayuda para ese cuando llegues ahi.
# -----------------------------------------------------------------------------
