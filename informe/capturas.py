"""Toma capturas de la aplicación corriendo en Docker (http://localhost:8080)."""
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8080"
ADMIN = ("admin@incidencias.local", sys.argv[1])


def entrar(pg, email, clave):
    pg.goto(URL)
    pg.evaluate("localStorage.clear()")
    pg.goto(URL)
    pg.fill("input[name=email]", email)
    pg.fill("input[name=clave]", clave)
    pg.click("button:has-text('Entrar')")
    pg.wait_for_selector("header")


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2, locale="es-CO",
                    timezone_id="America/Bogota")
    pg.goto(URL)
    pg.evaluate("localStorage.clear()")
    pg.goto(URL)
    pg.wait_for_selector("form.login")
    pg.screenshot(path="img/01_login.png")

    entrar(pg, "prueba@ejemplo.com", "prueba12345")
    pg.click("nav button:has-text('Nuevo')")
    pg.fill("input[placeholder=Asunto]", "Website down")
    pg.fill("textarea", "Our main website is down and customers cannot place orders since 9 am.")
    pg.click("button:has-text('Crear y clasificar')")
    pg.wait_for_selector("text=Lo que sugirió la IA")
    pg.screenshot(path="img/02_nuevo_ticket.png", full_page=True)

    entrar(pg, *ADMIN)
    pg.wait_for_selector("table")
    pg.screenshot(path="img/03_lista.png", full_page=True)
    pg.click("td:has-text('Website down')")
    pg.wait_for_selector("text=Historial")
    pg.screenshot(path="img/04_detalle.png", full_page=True)
    pg.click("nav button:has-text('Dashboard')")
    pg.wait_for_selector("text=Calidad del modelo")
    pg.screenshot(path="img/05_dashboard.png", full_page=True)

    pg.goto("http://localhost:8000/docs")
    pg.wait_for_selector(".opblock", timeout=20000)
    pg.screenshot(path="img/06_swagger.png")
    b.close()
print("ok")
