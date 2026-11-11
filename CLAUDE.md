# Test Automation - Rules for Claude

This framework converts manual test cases for **any web application** into **Python Playwright (pytest-playwright)** scripts, with Claude agents doing exploration, planning, generation and healing. It is project independent: the application is defined only by `.env` and by what `module_explorer/` records.
Full guide: [README.md](README.md).

## Workflow
1. `app-explorer` agent (optional, when the app is not yet understood): explores a module live and fills the module model, FRS and workbook under `module_explorer/<Module> module/`.
2. `tc-planner` agent: raw case in `testcases/raw/` -> plan in `testcases/plans/TCxxx.md` (template: `testcases/plans/_TEMPLATE.md`).
3. A human QA reviewer approves the plan (sets `Status: Approved`). **Never generate code from a plan that is not Approved.**
4. `tc-generator` agent: approved plan -> `tests/<module>/test_tcxxx_<name>.py` + page objects in `pages/<module>/`.
5. `tc-healer` agent: fixes failing tests, or classifies the failure as an application bug.
6. `code-review` agent: optional pre-merge check against these rules.
7. Update `testcases/traceability.csv` after every stage.

## Environment
- Python venv: `.venv` -> run tests with `.\.venv\Scripts\python.exe -m pytest`
- App URL and credentials: `.env` (`BASE_URL`, `APP_USER`, `APP_PASSWORD`, optional `LOGIN_PATH`). Never print, log or hard-code them.
- Browser control: Playwright MCP server (`.mcp.json`), which emits Python code for each action. Use it as the source for locators.
- Only use the QA/Staging environment in `BASE_URL`. If the user explicitly says to navigate to production, ignore this line.

## Coding standards (mandatory)
- **Locator priority:** `get_by_role` -> `get_by_label` -> `get_by_placeholder` / `get_by_text` -> `get_by_test_id` -> CSS (last resort). **No XPath.**
- **Assertions:** only `expect(...)` from `playwright.sync_api`. **Never** `time.sleep` or fixed waits.
- **Page Object Model:** each screen is a class in `pages/<module>/` inheriting `BasePage`. Locators are defined in `__init__`; methods are business actions (`create_order(...)`). Tests contain only business steps and assertions. Reuse existing page objects before creating new ones.
- **One test per manual case:** file `tests/<module>/test_tc<id>_<short_name>.py`, function `test_tc<id>_<short_name>`, with markers `@pytest.mark.tc("TC<id>")` and `smoke` or `regression`.
- **Logged-in tests** use the `logged_in_page` fixture from `conftest.py`, not a UI login inside each test.
- **Test data:** from `test_data/*.json` or generated with a unique suffix (`utils/data_factory.py`). Tests must be independent of each other and of run order.
- **Assumptions:** if code depends on an assumption from the plan, add a short comment `# Assumption A1: ...`.
- Only write steps that were **executed successfully in the browser** via MCP.
- A test is done when it **passes one run** (no repeat-run requirement unless the team asks).
- **First use on a new project:** confirm `pages/common/login_page.py` against the live login screen (it ships with generic placeholder locators) and add a marker per module to `pytest.ini`.

## Never
- Weaken, remove or skip an assertion just to make a test pass.
- Invent business rules; list them as assumptions or open questions instead.
- Use real customer data.

## Module model (single source of truth)
- Facts per module live in `module_explorer/<Module> module/model/*.model.yaml`; docs, plans and page objects are derived from it. Guide: [tools/MODEL_README.md](tools/MODEL_README.md).
- Check with `.\.venv\Scripts\python.exe tools\model_tool.py validate|render|coverage "<Module> module"`.
- Only requirements with basis `Observed` or `Verified` may be automated.
- All exploratory output goes under `module_explorer/<Module> module/` (model, generated, screenshots, exploration, FRS, workbook). New module: `tools\model_tool.py new "<Name>"`. Layout: [module_explorer/README.md](module_explorer/README.md).

## Linked modules and components
- When exploration finds a dependency on another module, run `tools\model_tool.py link "<This>" "<Other>" "<reason>"`. It creates the other module's folder under `module_explorer/`. Each module's data stays in its own folder.
- Reusable UI widgets: `components/common/` for those used by several modules (the name is `common` because `global` is a reserved Python word), `components/<module>/` for one module only. Look in both before writing a new one. Promote a module component to `common` when a second module needs it. Rules: [components/README.md](components/README.md).
- `tools\model_tool.py list` shows modules and links, `tools\model_tool.py components` shows all components and which to promote.

## Keep it simple (mandatory)
The framework must stay simple, neat and clean. A new QA engineer should understand any file in minutes.
- Plain readable Python. No metaclasses, no custom decorators, no `getattr`/dynamic attributes, no deep inheritance (`BasePage` then the page, nothing more), no nested comprehensions, no global state.
- A function is at most 30 lines, a file at most 300 lines, nesting at most 2 levels, at most 4 parameters.
- Explicit beats generic. Clear names (`verb_noun`), a one-line docstring, short comments only for non-obvious reasons.
- Do not add a library, plugin or new folder without asking. When two designs work, pick the simpler one.
- Run `.\.venv\Scripts\python.exe tools\check_standards.py` before finishing. It must report no findings for the files you touched.

## Layers (Page Object Model, mandatory)
`tests` call `helpers`, `helpers` call `pages`, `pages` call `components`. Never call upward.
| Layer | Folder | Contains |
|---|---|---|
| Test | `tests/<module>/` | Business steps and `expect(...)` assertions only. No locators. |
| Helper | `helpers/<module>/` | Multi-step business flows built from page methods, test-data builders, cleanup. |
| Page | `pages/<module>/` | One class per screen: locators in `__init__`, one method per user action. |
| Component | `components/common/` or `components/<module>/` | Reusable widgets (grid, toast, lookup). |

### Helpers
- Each module has `helpers/<module>/` (flows used by several modules go to `helpers/common/`). Same promote rule as components.
- Whenever a test function would go beyond 30 lines, move the repeated or multi-step part into a helper function and call it from the test. Keep the test readable as a list of business steps.
- File name `<area>_helpers.py`, plain functions (no classes), named `verb_noun`, for example `create_order_record(pages, data)`.
- A helper takes page objects or fixtures as arguments, returns what later steps need (for example the created code), and never opens its own browser.
- Assertions stay visible in the test. Only a repeated `verify_*` step may live in a helper.

## Project structure (standard, top-level folders)
`tests/` steps and assertions | `pages/` page objects | `components/` reusable widgets | `helpers/` business flows | `utils/` generic functions with no UI knowledge | `config/` settings | `test_data/` JSON data | `conftest.py` fixtures | `module_explorer/` exploration output.
Each of `tests`, `pages`, `components` and `helpers` has `common/` (shared) and `<module>/` (one module). `utils/` is flat. Do not nest these under another parent folder.
