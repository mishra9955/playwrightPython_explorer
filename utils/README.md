# utils

Generic plain functions that know nothing about the application or the browser.

- Allowed: unique-suffix and timestamp generators, reading JSON, string and date formatting, file paths.
- Not allowed: anything that takes a `page` or a locator. That belongs in `components/` or `pages/`.
- Flat folder, plain functions, no classes, one small file per theme (for example `data_utils.py`, `file_utils.py`).
- Do not add a util that duplicates one that exists. Check this folder first.
