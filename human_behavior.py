"""
Módulo para simular comportamiento humano en Playwright.
Evita detección de bots mediante:
- Movimientos de mouse realistas
- Delays aleatorios
- Scroll natural
- Comportamiento errático ocasional
"""

import asyncio
import random
from playwright.async_api import Page, Locator


async def human_delay(min_sec: float = 0.5, max_sec: float = 2.0):
    """Espera aleatoria para simular pensamiento humano."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def move_mouse_naturally(page: Page, to_x: int, to_y: int, steps: int = 20):
    """
    Mueve el mouse de forma natural con curva bezier.
    """
    # Obtener posición actual (simulada)
    from_x = random.randint(100, 500)
    from_y = random.randint(100, 500)

    for i in range(steps):
        t = i / steps
        # Curva bezier cuadrática para movimiento natural
        control_x = (from_x + to_x) / 2 + random.randint(-50, 50)
        control_y = (from_y + to_y) / 2 + random.randint(-50, 50)

        x = (1-t)**2 * from_x + 2*(1-t)*t * control_x + t**2 * to_x
        y = (1-t)**2 * from_y + 2*(1-t)*t * control_y + t**2 * to_y

        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.001, 0.01))


async def human_click(page: Page, locator: Locator, description: str = "elemento"):
    """
    Click con comportamiento humano:
    - Scroll al elemento
    - Hover sobre él
    - Pequeño delay
    - Click
    """
    print(f"  🖱️  Haciendo click en {description}...")

    # Scroll al elemento de forma natural
    await locator.scroll_into_view_if_needed()
    await human_delay(0.3, 0.8)

    # Obtener posición del elemento
    box = await locator.bounding_box()
    if box:
        # Mover mouse al elemento
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2

        # Agregar pequeña variación (no click en el centro exacto)
        target_x = center_x + random.randint(-10, 10)
        target_y = center_y + random.randint(-10, 10)

        await move_mouse_naturally(page, int(target_x), int(target_y))

    # Hover
    await locator.hover()
    await human_delay(0.2, 0.5)

    # Click
    await locator.click()
    await human_delay(0.3, 0.7)


async def human_type(page: Page, locator: Locator, text: str, description: str = "campo"):
    """
    Escribe texto de forma humana:
    - Click en el campo
    - Escribe letra por letra con delays variables
    - Ocasionalmente comete errores y los corrige
    """
    print(f"  ⌨️  Escribiendo en {description}: {text}")

    # Click en el campo
    await human_click(page, locator, description)

    # Limpiar campo
    await locator.clear()
    await human_delay(0.2, 0.4)

    # Escribir con delays realistas
    for i, char in enumerate(text):
        # 5% de probabilidad de "error humano"
        if random.random() < 0.05 and i > 0:
            # Escribir caracter incorrecto
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            await locator.press_sequentially(wrong_char, delay=random.randint(50, 150))
            await human_delay(0.1, 0.3)
            # Borrar
            await page.keyboard.press('Backspace')
            await human_delay(0.1, 0.2)

        # Escribir caracter correcto
        await locator.press_sequentially(char, delay=random.randint(80, 200))

        # Pausa ocasional (como si estuviera pensando)
        if random.random() < 0.1:
            await human_delay(0.3, 0.8)

    await human_delay(0.3, 0.6)


async def human_scroll(page: Page, direction: str = "down", amount: int = 300):
    """
    Scroll natural de la página.
    """
    print(f"  📜 Scrolling {direction}...")

    if direction == "down":
        for _ in range(5):
            await page.mouse.wheel(0, amount // 5)
            await human_delay(0.1, 0.3)
    else:
        for _ in range(5):
            await page.mouse.wheel(0, -(amount // 5))
            await human_delay(0.1, 0.3)

    await human_delay(0.5, 1.0)


async def random_mouse_movement(page: Page):
    """
    Movimientos aleatorios del mouse para parecer más humano.
    """
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 1000)
        y = random.randint(100, 800)
        await page.mouse.move(x, y)
        await human_delay(0.1, 0.3)


async def simulate_reading_time(min_sec: float = 2.0, max_sec: float = 5.0):
    """
    Simula tiempo de lectura/pensamiento.
    """
    wait_time = random.uniform(min_sec, max_sec)
    print(f"  🤔 Esperando {wait_time:.1f}s (simulando lectura)...")
    await asyncio.sleep(wait_time)
