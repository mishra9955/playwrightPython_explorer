import re

from playwright.sync_api import Page, expect

from config.settings import settings
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Login screen. TODO per project: confirm the locators and the post-login URL in the live app.

    Default locators assume a standard form (labels "Username"/"Password", button "Login").
    Replace them with what the Playwright MCP snapshot shows, keeping the locator priority in CLAUDE.md.
    """

    path = settings.login_path

    def __init__(self, page: Page):
        super().__init__(page)
        self.username = page.get_by_label("Username")
        self.password = page.get_by_label("Password")
        self.login_btn = page.get_by_role("button", name="Login")

    def login(self, username: str, password: str):
        """Fill the form, submit, and wait until the app has left the login page."""
        self.username.fill(username)
        self.password.fill(password)
        expect(self.login_btn).to_be_enabled()
        self.login_btn.click()
        expect(self.page).not_to_have_url(re.compile(re.escape(self.path)))
