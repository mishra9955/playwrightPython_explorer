# components

Reusable UI widgets (Playwright wrappers). They take a `page` or a root locator and never contain test assertions.

```
components/
  common/     GLOBAL components used by more than one module (DataGrid, Toast, ConfirmDialog, ...)
  <module>/   components used by ONE module only, e.g. components/orders/ for the order-notes card
```
The shared folder is called `common`, not `global`, because `global` is a reserved Python word and cannot be imported.

## Placement rules
1. Start module-specific: put a new component in `components/<module>/`.
2. Promote to `components/common/` as soon as a second module needs it. Move the file, fix imports, update the model.
3. Check `components/common/` and the module folder before writing a new component. Never duplicate.
4. Components do not import page objects. Page objects import components.
5. Module folder names are lower snake case and match `pages/<module>/` and `tests/<module>/`.

## Import
```python
from components.common.toast import Toast
from components.orders.order_notes_card import OrderNotesCard
```

## Record in the model
Every reusable widget found during exploration is listed under `components:` in the module model with
scope (`global` or `module`), owner, modules that use it, planned path and status (`exists` or `planned`).
`tools\model_tool.py components` prints all components across modules and flags ones to promote.
