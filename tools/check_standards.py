"""Simple standards check for pages/, components/, helpers/, utils/ and tests/.

Run from the project root:
  .\\.venv\\Scripts\\python.exe tools\\check_standards.py

Rules (see CLAUDE.md): functions max 30 lines, files max 300 lines,
no time.sleep, no XPath. Exit code 1 when something is found.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = ["pages", "components", "helpers", "utils", "tests"]
MAX_FUNCTION, MAX_FILE = 30, 300


def check(path):
    text = path.read_text(encoding="utf-8-sig")
    name = path.relative_to(ROOT)
    found = []
    if len(text.splitlines()) > MAX_FILE:
        found.append(f"{name}: file has {len(text.splitlines())} lines (max {MAX_FILE})")
    if "time.sleep" in text:
        found.append(f"{name}: time.sleep is not allowed")
    if re.search(r"xpath|locator\(\s*[\"']//", text, re.I):
        found.append(f"{name}: XPath is not allowed")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef):
            size = node.end_lineno - node.lineno + 1
            if size > MAX_FUNCTION:
                found.append(f"{name}::{node.name}: {size} lines (max {MAX_FUNCTION}), extract helper methods")
    return found


def main():
    problems = []
    for folder in FOLDERS:
        for path in sorted((ROOT / folder).rglob("*.py")):
            problems += check(path)
    print("\n".join(problems) if problems else "OK: no violations")
    print(f"{len(problems)} finding(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
