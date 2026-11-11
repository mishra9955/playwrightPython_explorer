from playwright.sync_api import Locator, Page, expect


class DataGrid:
    """Generic HTML table / grid: rows, headers, cell text, row count.

    Starting point only. Add the project's grid specifics here (filter boxes, paging, sorting,
    toolbar buttons) once they are verified live, and wait on the data API response, never a fixed delay.
    The expect_* methods only wait for state; business assertions stay in the tests.
    """

    def __init__(self, page: Page, root: Locator | None = None):
        self.page = page
        self.root = root or page.get_by_role("table").first
        self.rows = self.root.get_by_role("row")
        self.column_headers = self.root.get_by_role("columnheader")

    def row_with_text(self, text: str) -> Locator:
        """The row containing the given text (use the run's unique key, never 'first row')."""
        return self.rows.filter(has_text=text)

    def cell(self, row_text: str, column_name: str) -> Locator:
        """Cell of the row identified by `row_text`, in the column named `column_name`."""
        headers = [t.strip() for t in self.column_headers.all_inner_texts()]
        return self.row_with_text(row_text).get_by_role("cell").nth(headers.index(column_name))

    def expect_row_visible(self, text: str):
        expect(self.row_with_text(text)).to_be_visible()

    def expect_row_count(self, n: int):
        expect(self.rows).to_have_count(n)
