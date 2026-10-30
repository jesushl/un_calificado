from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from test_login import open_page


def test_index_shows_popular_providers_and_work_photos(browser, base_url):
    open_page(browser, f"{base_url}/")
    wait = WebDriverWait(browser, 8)
    heading = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
    assert "vuelta de tu casa" in heading.text.lower()
    assert browser.find_element(By.ID, "populares-titulo")
    assert browser.find_element(By.ID, "obras-titulo")
    photos = browser.find_elements(By.CSS_SELECTOR, ".obra-muro img")
    assert photos, "El índice debe mostrar fotos de obra"
    contact = browser.find_element(By.LINK_TEXT, "Entra para contactar")
    contact.click()
    wait.until(EC.url_contains("/entrar"))
    assert browser.find_element(By.NAME, "email")
    assert browser.find_element(By.CSS_SELECTOR, "[data-network='google']")
    assert browser.find_element(By.CSS_SELECTOR, "[data-network='facebook']")
    assert browser.find_element(By.CSS_SELECTOR, "[data-network='tiktok']")
