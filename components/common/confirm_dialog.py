from playwright.sync_api import Page, expect


class ConfirmDialog:
    """Yes / No confirmation dialog (delete, unsaved-data warnings). Adjust button names per app."""

    def __init__(self, page: Page):
        self.dialog = page.get_by_role("alertdialog")  # dialogs with alertdialog/dialog; adjust per app
        self.yes = self.dialog.get_by_role("button", name="Yes")
        self.no = self.dialog.get_by_role("button", name="No")

    def expect_text(self, text: str):
        expect(self.dialog).to_contain_text(text)

    def confirm(self):
        self.yes.click()

    def decline(self):
        self.no.click()
