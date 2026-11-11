# Playwright MCP Test Automation Framework

A project-independent framework that turns manual test cases for **any web application** into maintainable **Python Playwright (pytest-playwright)** tests. Claude agents do the repetitive work (exploring the app, planning, generating, healing). People approve every plan that matters.

It was derived from a working framework built for a large enterprise web application, with everything application-specific removed. You can hand this folder to a new engineer: follow [Quick start](#quick-start) and they can begin.

## Contents
1. [What you get](#what-you-get)
2. [Quick start](#quick-start)
3. [How the workflow works](#how-the-workflow-works)
4. [Agents](#agents)
5. [Architecture and folders](#architecture-and-folders)
6. [Using it on a new project (checklist)](#using-it-on-a-new-project-checklist)
7. [Coding standards](#coding-standards)
8. [The module model](#the-module-model)
9. [Test data and credentials](#test-data-and-credentials)
10. [Running tests and reports](#running-tests-and-reports)
11. [Command cheat sheet](#command-cheat-sheet)
12. [Worked example: your first test](#worked-example-your-first-test)
13. [Safety rules](#safety-rules)
14. [Troubleshooting](#troubleshooting)

## What you get
- **Layered Page Object Model**: Tests -> Helpers -> Pages -> Components, never upward.
- **Five Claude agents** in `.claude/agents/`: `app-explorer`, `tc-planner`, `tc-generator`, `tc-healer`, `code-review`.
- **Playwright MCP server** (`.mcp.json`) so agents drive a real browser and emit Python locators.
- **Module model** (YAML) as single source of truth, with a CLI (`tools/model_tool.py`) to scaffold, validate, render docs, link modules and report coverage.
- **Standards checker** (`tools/check_standards.py`) enforcing function and file size, no `time.sleep`, no XPath.
- **Fixtures** in `conftest.py`: one login per session, `logged_in_page`, `cleanup` (runs even when the test fails).
- **Reporting**: HTML report plus trace, screenshot and video on failure.
- **Self-check test** that proves the install works without needing any application.

Core principles: evidence before code (only steps seen working in a browser are automated), one source of truth per module, humans approve and agents execute, simple beats clever, safe in a shared environment.

## Quick start

### Prerequisites
- Windows with PowerShell (the commands use `.\.venv\Scripts\python.exe`; on macOS/Linux use `.venv/bin/python`)
- Python 3.10 or newer
- Node.js (for `npx`, which starts the Playwright MCP server)
- Claude Code (CLI or VS Code extension), opened in this folder so it reads `CLAUDE.md`, `.mcp.json` and `.claude/agents/`

### Setup (one time)
```powershell
cd <path-to>\playwright_MCP_framework
.\setup.ps1
```
`setup.ps1` creates `.venv`, installs `requirements.txt`, installs the Chromium browser, copies `.env.example` to `.env`, and runs the self-check. Manual equivalent:
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pytest -m selfcheck
```

### Configure the application
Edit `.env` (never commit it, it is git-ignored):
```
BASE_URL=https://your-qa-environment.example.com
APP_USER=your_qa_user
APP_PASSWORD=your_qa_password
LOGIN_PATH=/login
```
Use the **QA / staging** environment only.

### Confirm the install
```powershell
.\.venv\Scripts\python.exe -m pytest -m selfcheck       # passes without any application
.\.venv\Scripts\python.exe tools\check_standards.py     # OK: no violations
```

## How the workflow works
Each stage has one owner and one output, and `testcases/traceability.csv` is updated after every stage.

```
 1 Explore          2 Plan            3 Approve            4 Generate          5 Heal
 app-explorer  -->  tc-planner  -->   QA reviewer    -->   tc-generator  -->   tc-healer
 writes the model   plan in Draft     Status: Approved     test + pages        fix / report bug
```

| Stage | Input | Output | Who |
|---|---|---|---|
| 1 Explore (optional) | module name and goal | model YAML, FRS .docx, E2E workbook .xlsx, screenshots, notes in `module_explorer/<Module> module/` | `app-explorer` |
| 2 Plan | raw case in `testcases/raw/` | `testcases/plans/TC<id>.md` with `Status: Draft`, atomic steps, assumptions, open questions | `tc-planner` |
| 3 Approve | the plan | `Status: Approved` | **human QA reviewer** |
| 4 Generate | approved plan | `tests/<module>/test_tc<id>_<name>.py`, page objects, helpers | `tc-generator` |
| 5 Heal | failing test | fix, or an application bug write-up in `bugs/` and a strict `xfail` | `tc-healer` |

Hard rule: **never generate code from a plan that is not Approved.**

## Agents
Invoke them by name in Claude Code, for example: `Use the tc-planner agent on testcases/raw/login_cases.xlsx, case TC001`.

| Agent | Use when | Never does |
|---|---|---|
| `app-explorer` | You must understand a module before planning. Give it a module and a goal. | Writes test code. Changes data it did not create. |
| `tc-planner` | You have a raw manual case. | Writes code. Marks a plan Approved. Invents business rules. |
| `tc-generator` | A plan is Approved. | Writes a step it did not run live. Weakens assertions. |
| `tc-healer` | A test fails or is flaky. | Removes or skips an assertion. Hides an app bug. |
| `code-review` | Pre-merge or "review my test". | Fixes failing tests (use `tc-healer`). |

Agents are plain Markdown files in `.claude/agents/`. Edit them to tune behaviour for your team.

## Architecture and folders

```
 Tests        tests/<module>/        Business steps and expect(...) only, no locators
    |
    v
 Helpers      helpers/<module>/      Multi-step business flows, data builders, cleanup
    |
    v
 Pages        pages/<module>/        One class per screen, inherits BasePage
    |
    v
 Components   components/common/     Reusable widgets (grid, toast, dialog, lookup)
              components/<module>/   Widgets used by one module only

 Supports every layer: conftest.py (fixtures), config/settings.py, utils/, test_data/, module model
```

| Folder / file | Purpose |
|---|---|
| `tests/` | Test files, `tests/<module>/smoke` and `regression`. Ships with `test_selfcheck.py`. |
| `pages/` | `base_page.py`, `common/login_page.py` (generic placeholder, confirm per project), one folder per module. |
| `components/` | `common/` ships with `DataGrid`, `Toast`, `ConfirmDialog`. [Rules](components/README.md). |
| `helpers/` | Business flows as plain functions. [Rules](helpers/README.md). |
| `utils/` | Generic functions with no UI knowledge: `data_factory.py` (unique names/numbers), `data_loader.py` (JSON). |
| `config/settings.py` | Reads `.env`: base URL, user, password, login path, timeout. |
| `test_data/` | JSON test data. `users.json` maps roles to `.env` variable names. |
| `conftest.py` | Fixtures: `base_url`, `credentials`, `auth_state`, `logged_in_page`, `cleanup`. |
| `testcases/` | `raw/` (manual cases as received), `plans/` (+ `_TEMPLATE.md`), `traceability.csv`. |
| `module_explorer/` | One folder per explored module. Starts empty. [Layout](module_explorer/README.md). |
| `tools/` | `model_tool.py`, `check_standards.py`, [MODEL_README.md](tools/MODEL_README.md). |
| `bugs/` | Application defect write-ups. [Rules](bugs/README.md). |
| `auth/`, `reports/` | Saved login state and run output. Git-ignored. |
| `.claude/` | Agents and local Claude Code permissions. |
| `.mcp.json` | Playwright MCP server: Python codegen, Chromium, 1440x900 viewport, `data-testid` as test id attribute. |
| `pytest.ini` | Chromium, tracing/screenshot/video on failure, HTML report, markers. |
| `CLAUDE.md` | The rules Claude follows in this repo. Read it, it is short. |

Fixtures in `conftest.py`:
- `logged_in_page`: a page already logged in, from a session-wide saved login state. Use it in every logged-in test.
- `cleanup`: a list; append lambdas that delete what the test created. They run in reverse order even if the test fails.

## Using it on a new project (checklist)
1. Copy this folder (without `.venv`, `.env`, `auth/*.json`, `reports/`) and run `.\setup.ps1`.
2. Fill `.env` with the QA `BASE_URL` and a test user.
3. Open the folder in Claude Code. Ask it to explore the login screen with Playwright MCP, then fix `pages/common/login_page.py` (it ships with placeholder locators: labels "Username"/"Password", button "Login", and "URL leaves the login path" as the success check).
4. Check `BasePage.expect_title` and the toast/dialog components against the real UI; adapt once, in `components/common/`.
5. Add a pytest marker per module in `pytest.ini`.
6. If the app's UI library needs special handling (custom dropdowns, virtual grids, masked inputs), record it as a pattern in the module model and in the shared component.
7. Run `app-explorer` on the first module: `Use the app-explorer agent on the "Orders" module, goal: understand list and create screens`.
8. Put manual cases in `testcases/raw/`, then plan, approve, generate.
9. Commit the framework; keep project facts in `module_explorer/`.

Nothing in the framework code names a product. Project facts live only in `.env`, `test_data/`, `module_explorer/` and the pages, components and helpers you add.

## Coding standards
Enforced by `CLAUDE.md` for agents, by `tools/check_standards.py` for the mechanical parts, and by the `code-review` agent.

- **Locator priority:** `get_by_role` -> `get_by_label` -> `get_by_placeholder` / `get_by_text` -> `get_by_test_id` -> CSS (last resort). **No XPath.**
- **Assertions:** only `expect(...)`. **No `time.sleep`, no fixed waits.** Wait on state or on the API response.
- **POM:** locators in `__init__`; methods are business actions; tests hold only business steps and assertions.
- **One test per manual case:** `tests/<module>/test_tc<id>_<name>.py`, function `test_tc<id>_<name>`, markers `@pytest.mark.tc("TC<id>")` and `smoke` or `regression`.
- **Independence:** unique data per run (timestamp suffix), clean up what you create, find records by your unique value, never "first row".
- **Assumptions** from the plan appear as `# Assumption A1: ...`; requirements as `# Req: FR-<MOD>-nnn`.
- **Size:** function max 30 lines, file max 300, nesting max 2, max 4 parameters.
- **Never:** weaken or skip an assertion to make a test pass, invent business rules, use real customer data.

## The module model
One YAML per module is the single source of truth: `module_explorer/<Module> module/model/<module>.model.yaml` holds screens, fields, locators, rules, requirements (`FR-<MOD>-nnn`), reusable components, open questions and test data. Docs, plans and page objects are derived from it.

Requirement **basis**: `Observed` (seen live), `Verified` (executed), `Spec` (documents only), `Assumption`, `Blocked`. **Only Observed and Verified may be automated.**

```powershell
.\.venv\Scripts\python.exe tools\model_tool.py new "Orders"                       # scaffold module
.\.venv\Scripts\python.exe tools\model_tool.py validate "Orders module"           # check the model
.\.venv\Scripts\python.exe tools\model_tool.py render "Orders module"             # write generated/*.md
.\.venv\Scripts\python.exe tools\model_tool.py coverage "Orders module"           # ready to automate vs needs verification
.\.venv\Scripts\python.exe tools\model_tool.py link "Orders" "Customers" "needs a customer" Verified
.\.venv\Scripts\python.exe tools\model_tool.py list                               # all modules and links
.\.venv\Scripts\python.exe tools\model_tool.py components                         # components, and which to promote
```
Full guide: [tools/MODEL_README.md](tools/MODEL_README.md). The model can also cite application source code as a second, separate evidence (`code:` list); code evidence never makes a requirement automatable by itself.

## Test data and credentials
- Credentials and URL live **only** in `.env`. Never print, log or hard-code them.
- Role-specific users: add `ADMIN_USER` / `ADMIN_PASSWORD` to `.env` and map the role in `test_data/users.json`.
- Test data: JSON files in `test_data/<module>/`, read with `utils.data_loader.load("<module>/<file>")`. Unique values from `utils/data_factory.py` (`unique_name`, `unique_number`, `stamp`).
- Explorer-created records use the prefix `AUTOEXP` and are logged in `created_resources.md`.

## Running tests and reports
```powershell
.\.venv\Scripts\python.exe -m pytest                              # everything
.\.venv\Scripts\python.exe -m pytest -m smoke                     # smoke only
.\.venv\Scripts\python.exe -m pytest -m "regression and orders"   # needs an 'orders' marker in pytest.ini
.\.venv\Scripts\python.exe -m pytest tests\orders\smoke\test_tc001_order_lifecycle.py
.\.venv\Scripts\python.exe -m pytest --headed --slowmo 300        # watch it run
```
Output: `reports/report.html` (self-contained), `reports/test-results/` (trace.zip, screenshots, videos for failures). Open a trace with `.\.venv\Scripts\python.exe -m playwright show-trace <trace.zip>`.

Tests that change shared configuration are marked `serial`; do not run them in parallel.

## Command cheat sheet
| Goal | Command |
|---|---|
| First-time setup | `.\setup.ps1` |
| Self-check | `.\.venv\Scripts\python.exe -m pytest -m selfcheck` |
| Standards check | `.\.venv\Scripts\python.exe tools\check_standards.py` |
| New module | `.\.venv\Scripts\python.exe tools\model_tool.py new "<Name>"` |
| Run one test | `.\.venv\Scripts\python.exe -m pytest tests\<module>\<file>.py` |
| Debug in the browser | add `--headed --slowmo 300` |

## Worked example: your first test
1. Manual case saved in `testcases/raw/` (for example "TC001: create an order and see it in the list").
2. Ask Claude: `Use the tc-planner agent on TC001`. It explores the live app and writes `testcases/plans/TC001.md` (Draft).
3. You read the plan, answer the open questions, set `**Status:** Approved`.
4. Ask Claude: `Use the tc-generator agent on TC001`. It runs each step in the browser, then writes:
   - `pages/orders/orders_page.py` (locators in `__init__`, one method per action)
   - `helpers/orders/order_helpers.py` (multi-step flows, only if the test would exceed 30 lines)
   - `tests/orders/smoke/test_tc001_order_lifecycle.py`
5. The generated test looks like this:
```python
import pytest
from playwright.sync_api import expect

from pages.orders.orders_page import OrdersPage
from utils.data_factory import unique_name


@pytest.mark.tc("TC001")
@pytest.mark.smoke
def test_tc001_order_lifecycle(logged_in_page, cleanup):
    """Create an order and find it in the list."""
    orders = OrdersPage(logged_in_page).open()
    name = unique_name("AUTO_ORDER")
    orders.create_order(name)
    cleanup.append(lambda: orders.delete_order(name))

    expect(orders.row_for(name)).to_be_visible()
```
6. It passes one run. The generator sets the plan to `Automated` and updates `testcases/traceability.csv`.
7. If it breaks later, ask for `tc-healer`. It classifies the failure as a script issue (fixes it), an application bug (strict `xfail` plus a write-up in `bugs/`), or a plan issue (reports it).

## Safety rules
- QA / staging only. Production only when the user explicitly says so.
- Agents create, change and delete only their own records (prefix `AUTOEXP` or the caller's prefix).
- No changes to admin configuration, master data or other users' records without explicit approval.
- No bulk or batch actions that process other users' data. No payments or irreversible actions.
- No credentials in files, logs, screenshots or replies. Screenshots must not show personal data.
- A permission denial is a decision: report it, do not route around it.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `playwright` browser missing | `.\.venv\Scripts\python.exe -m playwright install chromium` |
| Tests skip with "APP_USER / APP_PASSWORD not set" | Fill `.env` |
| Login fails in `auth_state` | The placeholder `LoginPage` locators do not match your app: fix `pages/common/login_page.py` |
| MCP browser tools missing in Claude Code | Node.js not installed, or the project's `.mcp.json` was not approved: run `/mcp` and enable `playwright` |
| `ModuleNotFoundError: pages` | Run pytest from the project root |
| Stale login after a password change | Delete `auth/state.json` |
| `check_standards.py` reports a long function | Extract a helper or page method; do not raise the limit |
| Dropdown or masked input ignores `fill()` | Use `press_sequentially`; note it in the model so it is not rediscovered |
