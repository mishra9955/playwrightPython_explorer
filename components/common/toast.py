from playwright.sync_api import Page, expect


class Toast:
    """Transient notification messages (role=alert or role=status).

    Adjust the locators if the app's toast library exposes no ARIA role (CSS class as last resort).
    """

    def __init__(self, page: Page):
        self.root = page.get_by_role("alert")
        self.status = page.get_by_role("status")

    def expect_text(self, text: str):
        expect(self.root.or_(self.status)).to_contain_text(text)
