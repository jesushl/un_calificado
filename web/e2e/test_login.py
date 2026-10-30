import pytest
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def open_page(browser, url):
    try:
        browser.get(url)
    except WebDriverException as error:
        pytest.skip(f"Cliente web no disponible en {url}: {error}")


def test_login_page_renders_wordmark_and_form(browser, base_url):
    open_page(browser, f"{base_url}/entrar")

    wait = WebDriverWait(browser, 8)
    heading = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
    )
    assert "proyecto" in heading.text.lower()
    assert browser.find_element(By.NAME, "email")
    assert browser.find_element(By.NAME, "password")
    assert browser.find_element(By.CSS_SELECTOR, "button[type='submit']").text.strip() == "Entrar"


def test_empty_login_shows_field_error(browser, base_url):
    open_page(browser, f"{base_url}/entrar")
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    alert = WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[role='alert']"))
    )
    assert "correo" in alert.text.lower()


def test_register_offers_client_and_provider_roles(browser, base_url):
    open_page(browser, f"{base_url}/registro")
    wait = WebDriverWait(browser, 8)
    wait.until(EC.presence_of_element_located((By.NAME, "role")))
    labels = [item.text for item in browser.find_elements(By.CSS_SELECTOR, ".choice-title")]
    assert "Necesito un oficio" in labels
    assert "Ofrezco un oficio" in labels
