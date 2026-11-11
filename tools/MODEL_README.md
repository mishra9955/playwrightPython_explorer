# Module model: single source of truth

Each explored module keeps one structured file: `module_explorer/<Module> module/model/<module>.model.yaml`.
It holds screens, fields, locators, rules, requirements (`FR-<MOD>-nnn`), open questions and test data.

## Who reads and writes it
| Stage | Action |
|---|---|
| app-explorer | Writes facts into the model first (with a basis), then builds the FRS and workbook from it. |
| FRS / workbook builders | Import `load_model()` from `tools/model_tool.py`. They never retype facts. |
| tc-planner | Reads requirements and screens. Lists the requirement ids in the plan. |
| tc-generator | Takes locators from the model. Puts `# Req: FR-ORD-nnn` in each test. |
| tc-healer | Corrects a changed locator or rule in the model, then in the test. |

## Basis values
`Observed` seen live, `Verified` executed by action, `Spec` from source documents only, `Assumption`, `Blocked`.
Only `Observed` and `Verified` requirements may be automated. The others must be verified first.

## Code evidence (second source of truth)
The application source code can confirm a rule that the UI does not show (validation messages, field lengths, hidden triggers). Cite it on the requirement, separate from `basis`:
```
- id: FR-ORD-007
  basis: Spec            # basis still says what was seen in the UI
  code:
    - {file: "src/services/order_validator.py", note: "validate() rejects empty customer with message E1640"}
```
- `file` is relative to `module.code_root` in the model. `validate` warns when a cited file is missing.
- Code evidence never makes a requirement automatable. A requirement found in code but not seen in the UI keeps basis `Spec` until it is observed or verified live.
- `coverage` lists what was found in code but not yet seen in the UI (verify these next) and what was seen in the UI with no code evidence.

## Commands
```
.\.venv\Scripts\python.exe tools\model_tool.py validate "Orders module"
.\.venv\Scripts\python.exe tools\model_tool.py render   "Orders module"
.\.venv\Scripts\python.exe tools\model_tool.py coverage "Orders module"
```
`render` writes `generated/locators.md`, `screens.md` and `traceability.md`. Never edit those by hand.

## Adding a module
`.\.venv\Scripts\python.exe tools\model_tool.py new "<Name>"` creates `module_explorer/<Name> module/` with a skeleton model, `screenshots/` and `exploration/`. `list` shows all modules. See [module_explorer/README.md](../module_explorer/README.md).

## Linked modules and components
- `link "<A>" "<B>" "<reason>" [basis]` records that A depends on B, creates B's folder if needed, and writes `model/dependencies.yaml` for both. Facts about B stay in B's folder.
- The model's `components:` list holds each reusable widget with scope `global` (`components/common/`) or `module` (`components/<module>/`). `validate` checks paths and scope. `components` prints all of them and flags module components used by several modules.
- `render` also writes `generated/dependencies.md`.
