# bugs

Written-up application defects found while automating (the tc-healer classifies a failure as APPLICATION BUG).

- One file per defect: `BUG_<Module>_<short_title>_<yyyymmdd_hhmmss>.md`; screenshots in a sibling `screenshots_<yyyymmdd_hhmmss>/` folder.
- Content: steps to reproduce, expected vs actual, environment (from `BASE_URL`, never the URL itself if it is sensitive), the failing test, evidence.
- The failing test stays in the suite marked `@pytest.mark.xfail(reason="APP BUG: ...", strict=True)`. Never weaken the assertion.
