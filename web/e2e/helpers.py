from datetime import date, timedelta

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


DEMO_CLIENT = ("demo.cliente@example.com", "DemoPass123!")
DEMO_PROVIDER = ("demo.proveedor@example.com", "DemoPass123!")


def open_page(browser, url):
    try:
        browser.get(url)
    except WebDriverException as error:
        import pytest

        pytest.skip(f"Cliente web no disponible en {url}: {error}")


def wait_css(browser, selector, timeout=15):
    return WebDriverWait(browser, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def login(browser, base_url, email, password):
    import time

    last_alerts: list[str] = []
    for attempt in range(4):
        open_page(browser, f"{base_url}/entrar")
        wait_css(browser, "input[name='email']")
        fill_input(browser, browser.find_element(By.NAME, "email"), email)
        fill_input(browser, browser.find_element(By.NAME, "password"), password)
        browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(browser, 20).until(
            lambda driver: "/entrar" not in driver.current_url
            or driver.find_elements(By.CSS_SELECTOR, "[role='alert']")
        )
        if "/entrar" not in browser.current_url:
            return
        last_alerts = [el.text for el in browser.find_elements(By.CSS_SELECTOR, "[role='alert']")]
        if any("Demasiados intentos" in text for text in last_alerts):
            time.sleep(16)
            continue
        break
    raise AssertionError(f"Login falló para {email}: {last_alerts or browser.current_url}")


def logout(browser, base_url=None):
    browser.execute_script("sessionStorage.clear(); localStorage.clear();")
    if base_url:
        open_page(browser, f"{base_url}/entrar")
    else:
        buttons = browser.find_elements(By.XPATH, "//button[contains(., 'Cerrar sesión')]")
        if buttons:
            buttons[0].click()
        open_page(browser, browser.current_url.split("/entrar")[0].rstrip("/") + "/entrar" if "://" in browser.current_url else "/entrar")
    wait_css(browser, "input[name='email']")


def future_date_iso(days=10):
    return (date.today() + timedelta(days=days)).isoformat()


def future_local_slot(days=5, hour=10):
    # Día y minuto únicos para no chocar con citas CONFIRMADA de corridas previas.
    import time

    stamp = time.time_ns()
    offset_days = 90 + (stamp % 400)
    minute = (stamp // 1_000_000) % 50
    start_hour = 8 + ((stamp // 1_000) % 10)
    day = date.today() + timedelta(days=int(offset_days))
    start = f"{day.isoformat()}T{start_hour:02d}:{minute:02d}"
    end = f"{day.isoformat()}T{start_hour + 1:02d}:{minute:02d}"
    return start, end


def _react_set_value(browser, element, value):
    browser.execute_script(
        """
        const el = arguments[0];
        const value = arguments[1];
        const last = el.value;
        el.value = value;
        const tracker = el._valueTracker;
        if (tracker) tracker.setValue(last);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        element,
        value,
    )


def fill_input(browser, element, value):
    """Actualiza el value de inputs controlados por React."""
    browser.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    _react_set_value(browser, element, value)


def fill_datetime_local(browser, element, value):
    fill_input(browser, element, value)
