from playwright.sync_api import Page, expect


class BasePage:
    """Common behaviour shared by all page objects. Add only what EVERY screen needs."""

    path = "/"  # route of the screen, relative to BASE_URL; override in each page

    def __init__(self, page: Page):
        self.page = page

    def open(self):
        """Go to this screen's route."""
        self.page.goto(self.path)
        return self

    def expect_title(self, title: str):
        """The browser tab title matches (adjust here if the app uses a prefix, e.g. 'App: <title>')."""
        expect(self.page).to_have_title(title)
