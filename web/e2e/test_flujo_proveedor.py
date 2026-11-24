"""Agenda e inbox del prestador con cuentas demo."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import DEMO_PROVIDER, login, open_page, wait_css


def test_proveedor_ve_solicitudes_y_agenda(browser, base_url):
    login(browser, base_url, *DEMO_PROVIDER)

    open_page(browser, f"{base_url}/proyectos")
    wait_css(browser, "h1")
    assert "solicitudes" in browser.find_element(By.CSS_SELECTOR, "h1").text.lower()
    WebDriverWait(browser, 12).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid^='request-card-']"))
    )
    cards = browser.find_elements(By.CSS_SELECTOR, "[data-testid^='request-card-']")
    assert cards, "El inbox del proveedor debe listar solicitudes del seed o del flujo"

    open_page(browser, f"{base_url}/agenda")
    wait_css(browser, "[data-testid='agenda-page']")
    assert "citas" in browser.find_element(By.CSS_SELECTOR, "h1").text.lower()
    WebDriverWait(browser, 12).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid^='agenda-item-']"))
    )
    items = browser.find_elements(By.CSS_SELECTOR, "[data-testid^='agenda-item-']")
    assert items, "Con seed demo el prestador debe ver al menos una cita en agenda"
    items[0].click()
    wait_css(browser, "[data-testid='appointments-section']")
    assert "/proyectos/" in browser.current_url
    assert browser.find_elements(By.CSS_SELECTOR, "[data-testid='messages-section']")


def test_proveedor_nav_incluye_agenda(browser, base_url):
    login(browser, base_url, *DEMO_PROVIDER)
    open_page(browser, f"{base_url}/")
    link = WebDriverWait(browser, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "nav a[href='/agenda']"))
    )
    assert "agenda" in link.text.strip().lower()
    link.click()
    WebDriverWait(browser, 15).until(EC.url_contains("/agenda"))
    wait_css(browser, "[data-testid='agenda-page']", timeout=20)
