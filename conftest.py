import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Browser, Page

from pages.common.login_page import LoginPage

load_dotenv()

AUTH_FILE = Path("auth/state.json")


@pytest.fixture(scope="session")
def base_url():
    """Application URL, read from BASE_URL in .env."""
    return os.getenv("BASE_URL")


@pytest.fixture(scope="session")
def credentials():
    user, password = os.getenv("APP_USER"), os.getenv("APP_PASSWORD")
    if not user or not password:
        pytest.skip("APP_USER / APP_PASSWORD not set in .env")
    return {"username": user, "password": password}


@pytest.fixture(scope="session")
def auth_state(browser: Browser, base_url, credentials):
    """Log in once per test session and save cookies/storage for reuse."""
    if not base_url:
        pytest.skip("BASE_URL not set in .env")
    AUTH_FILE.parent.mkdir(exist_ok=True)
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    login = LoginPage(page)
    login.open()
    login.login(credentials["username"], credentials["password"])
    context.storage_state(path=AUTH_FILE)
    context.close()
    return str(AUTH_FILE)


@pytest.fixture
def logged_in_page(new_context, auth_state) -> Page:
    """A page that is already logged in (tracing/video/screenshot settings still apply)."""
    context = new_context(storage_state=auth_state)
    return context.new_page()


@pytest.fixture
def cleanup():
    """Register teardown callables; they run (LIFO) even when the test fails.

    Usage: cleanup.append(lambda: orders_page.delete_order(code))
    """
    actions: list = []
    yield actions
    for action in reversed(actions):
        try:
            action()
        except Exception as exc:  # teardown must never mask the real failure
            print(f"cleanup failed: {exc!r}")
