# module_explorer

All exploratory data lives here, one folder per module. Nothing about an explored module is kept outside this folder.

```
module_explorer/
  <Module> module/
    model/            <module>.model.yaml   single source of truth (screens, fields, locators, requirements)
    generated/        locators.md, screens.md, traceability.md   rendered from the model, never hand-edited
    screenshots/      every explored screen + INDEX.md
    exploration/      working notes: findings, created_resources.md, test data candidates, corrections
    <Module>_FRS.docx
    <Module>_E2E_Test_Cases.xlsx
```

The folder starts empty. Each module you explore adds one folder.

## Add a new module
```
.\.venv\Scripts\python.exe tools\model_tool.py new "Orders"      # scaffolds "Orders module"
.\.venv\Scripts\python.exe tools\model_tool.py list                     # all modules and their status
```
Then run the `app-explorer` agent with the module name. It fills the model, then builds the FRS and workbook from it.
Details: [tools/MODEL_README.md](../tools/MODEL_README.md).

## Linked modules
When a module depends on another one, the explorer runs:
```
.\.venv\Scripts\python.exe tools\model_tool.py link "Orders" "Customers" "Order needs a customer record" Verified
```
This creates `Customers module/` if missing and records the link on both sides in `model/dependencies.yaml`.
Facts about Customers go into the Customers folder only. Modules created this way start as `NOT_EXPLORED`.

## Components
Reusable widgets are listed per module under `components:` in the model and live in `components/common/` (several modules) or `components/<module>/` (one module). See [components/README.md](../components/README.md).
