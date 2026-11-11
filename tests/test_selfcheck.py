"""Framework sanity checks that do not need the application under test."""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.selfcheck
def test_browser_and_locators_work(page: Page):
    page.set_content(
        """
        <label for="u">Username</label><input id="u">
        <button onclick="document.getElementById('msg').hidden = false">Sign in</button>
        <p id="msg" hidden>Welcome</p>
        """
    )
    page.get_by_label("Username").fill("qa_user")
    page.get_by_role("button", name="Sign in").click()

    expect(page.get_by_label("Username")).to_have_value("qa_user")
    expect(page.get_by_text("Welcome")).to_be_visible()
