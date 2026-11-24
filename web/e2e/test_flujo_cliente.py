"""Flujo feliz: búsqueda → contratación → cierre → evaluación."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import (
    DEMO_CLIENT,
    DEMO_PROVIDER,
    fill_datetime_local,
    fill_input,
    future_date_iso,
    future_local_slot,
    login,
    logout,
    open_page,
    wait_css,
)


def test_cliente_contrata_presupuesto_sin_visita(browser, base_url):
    outcome = f"Sellado de humedad e2e {future_date_iso()}"

    login(browser, base_url, *DEMO_CLIENT)
    open_page(browser, f"{base_url}/")
    wait_css(browser, "#populares-titulo")
    WebDriverWait(browser, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".calificados .ficha"))
    )
    cards = browser.find_elements(By.CSS_SELECTOR, ".calificados .ficha")
    assert cards, "El índice debe listar calificados con seed"
    target = None
    for card in cards:
        if "Construcciones Demo MX" in card.text:
            target = card
            break
    assert target is not None, "Falta el proveedor demo en el índice"
    target.find_element(By.LINK_TEXT, "Solicitar cotización").click()
    wait_css(browser, "textarea[name='expectedOutcome']")
    fill_input(browser, browser.find_element(By.NAME, "expectedOutcome"), outcome)
    fill_input(browser, browser.find_element(By.NAME, "approximateZone"), "Coyoacán")
    fill_input(browser, browser.find_element(By.NAME, "desiredDate"), future_date_iso())
    # description a veces llega con altura 0 en headless; el contacto API ya pone texto por defecto.
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait_css(browser, "[data-testid='confirm-request']")
    assert "/proyectos/" in browser.current_url
    request_url = browser.current_url
    browser.find_element(By.CSS_SELECTOR, "[data-testid='confirm-request']").click()
    WebDriverWait(browser, 12).until(
        lambda driver: "confirmada"
        in driver.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text.lower()
    )

    logout(browser, base_url)
    login(browser, base_url, *DEMO_PROVIDER)
    open_page(browser, f"{base_url}/proyectos")
    wait_css(browser, "h1")
    needle = outcome.lower()

    def find_request_card(driver):
        for card in driver.find_elements(By.CSS_SELECTOR, "[data-testid^='request-card-']"):
            if needle in card.text.lower():
                return card
        return False

    card = WebDriverWait(browser, 12).until(find_request_card)
    card.click()
    wait_css(browser, "[data-testid='accept-request']")
    browser.find_element(By.CSS_SELECTOR, "[data-testid='accept-request']").click()
    wait_css(browser, "[data-testid='create-proposal-form']")
    form = browser.find_element(By.CSS_SELECTOR, "[data-testid='create-proposal-form']")
    form.find_element(By.NAME, "workDescription").send_keys("Sellado y pintura del muro norte")
    form.find_element(By.NAME, "labor").clear()
    form.find_element(By.NAME, "labor").send_keys("1200")
    form.find_element(By.NAME, "materials").clear()
    form.find_element(By.NAME, "materials").send_keys("300")
    form.find_element(By.NAME, "extras").clear()
    form.find_element(By.NAME, "extras").send_keys("0")
    form.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(browser, 12).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid^='proposal-']"))
    )
    assert "enviada" in browser.find_element(By.CSS_SELECTOR, "[data-testid='proposals-section']").text.lower()

    starts, ends = future_local_slot(days=20, hour=9)
    visit = browser.find_element(By.CSS_SELECTOR, "[data-testid='propose-visit-form']")
    fill_datetime_local(browser, visit.find_element(By.NAME, "visitStarts"), starts)
    fill_datetime_local(browser, visit.find_element(By.NAME, "visitEnds"), ends)
    fill_input(browser, visit.find_element(By.NAME, "visitCost"), "0")
    visit.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(browser, 12).until(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, "[data-testid^='appointment-']")
        or driver.find_elements(By.CSS_SELECTOR, ".alert--danger")
    )
    alerts = browser.find_elements(By.CSS_SELECTOR, ".alert--danger")
    assert not alerts, alerts[0].text if alerts else ""
    assert browser.find_elements(By.CSS_SELECTOR, "[data-testid^='appointment-']")

    logout(browser, base_url)
    login(browser, base_url, *DEMO_CLIENT)
    open_page(browser, request_url)
    wait_css(browser, "[data-testid='accept-proposal']")
    browser.find_element(By.CSS_SELECTOR, "[data-testid='accept-proposal']").click()
    WebDriverWait(browser, 12).until(
        lambda driver: "aceptada"
        in driver.find_element(By.CSS_SELECTOR, "[data-testid='proposals-section']").text.lower()
    )
    confirm_appt = browser.find_elements(By.CSS_SELECTOR, "[data-testid='confirm-appointment']")
    if confirm_appt:
        confirm_appt[0].click()
        WebDriverWait(browser, 12).until(
            lambda driver: "confirmada"
            in driver.find_element(By.CSS_SELECTOR, "[data-testid='appointments-section']").text.lower()
        )
    wait_css(browser, "[data-testid='message-input']")
    fill_input(
        browser,
        browser.find_element(By.CSS_SELECTOR, "[data-testid='message-input']"),
        "Quedamos para la visita, gracias.",
    )
    browser.find_element(By.CSS_SELECTOR, "[data-testid='send-message']").click()
    WebDriverWait(browser, 12).until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, "[data-testid='message-list']"), "Quedamos para la visita"
        )
    )
    WebDriverWait(browser, 12).until(
        lambda driver: "programado"
        in driver.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text.lower()
    )

    logout(browser, base_url)
    login(browser, base_url, *DEMO_PROVIDER)
    open_page(browser, request_url)
    wait_css(browser, "[data-testid='work-section']", timeout=20)
    WebDriverWait(browser, 20).until(
        lambda driver: "programado"
        in driver.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text.lower()
        or "proceso"
        in driver.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text.lower()
    )
    if not browser.find_elements(By.CSS_SELECTOR, "[data-testid='start-work']"):
        status = browser.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text
        work = browser.find_element(By.CSS_SELECTOR, "[data-testid='work-section']").text
        proposals_txt = browser.find_element(By.CSS_SELECTOR, "[data-testid='proposals-section']").text
        raise AssertionError(f"Sin iniciar trabajo. status={status!r} work={work!r} proposals={proposals_txt!r}")
    start = browser.find_element(By.CSS_SELECTOR, "[data-testid='start-work']")
    browser.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", start)
    WebDriverWait(browser, 20).until(
        lambda driver: "proceso"
        in driver.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text.lower()
    )
    finish = wait_css(browser, "[data-testid='finish-work']", timeout=20)
    browser.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", finish)
    WebDriverWait(browser, 20).until(
        lambda driver: "terminado"
        in driver.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text.lower()
    )

    logout(browser, base_url)
    login(browser, base_url, *DEMO_CLIENT)
    open_page(browser, request_url)
    conclude = wait_css(browser, "[data-testid='conclude-work']", timeout=20)
    browser.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", conclude)
    wait_css(browser, "[data-testid='work-closed']", timeout=20)
    wait_css(browser, "[data-testid='evaluation-section']", timeout=20)
    fill_input(browser, browser.find_element(By.CSS_SELECTOR, "[data-testid='evaluation-score']"), "5")
    fill_input(
        browser,
        browser.find_element(By.CSS_SELECTOR, "[data-testid='evaluation-comment']"),
        "Quedó bien el sellado.",
    )
    browser.find_element(By.CSS_SELECTOR, "[data-testid='submit-evaluation']").click()
    wait_css(browser, "[data-testid='evaluation-done']", timeout=20)
    assert "concluido" in browser.find_element(By.CSS_SELECTOR, "[data-testid='project-status']").text.lower()
