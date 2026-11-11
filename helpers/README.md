# helpers

Multi-step business flows used by tests. Plain functions, no classes.

```
helpers/
  common/   flows used by several modules
  orders/   flows for the Orders module only (add <module>/ per new module)
```

## Rules
- A test function over 30 lines gets its repeated or multi-step part moved here.
- File `<area>_helpers.py`, function `verb_noun(pages, data)`. Return what later steps need.
- Helpers call page objects. Page objects call components. Never the other way round.
- Assertions stay in the test, except a repeated `verify_*` step.
- Start in `helpers/<module>/`. Move to `helpers/common/` when a second module needs it.

## Example
```python
# helpers/orders/order_helpers.py
def create_order_record(grid, detail, data):
    grid.open_create()
    detail.fill_order(data)
    detail.save_all()
    return data["order_number"]

# tests/orders/smoke/test_tc001_order_lifecycle.py
order = create_order_record(grid, detail, data)
expect(grid.row_for(order)).to_be_visible()
```
