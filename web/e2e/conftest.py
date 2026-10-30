import os

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

BASE_URL = os.environ.get("UX_BASE_URL", "http://127.0.0.1:5173")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL.rstrip("/")


@pytest.fixture
def browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--no-sandbox")
    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as error:
        pytest.skip(f"Chrome/Selenium no disponible: {error}")
    yield driver
    driver.quit()
