"""Module model tool: validate, render derived docs, report coverage.

Usage (from project root):
  .\\.venv\\Scripts\\python.exe tools\\model_tool.py validate "Orders module"
  .\\.venv\\Scripts\\python.exe tools\\model_tool.py render   "Orders module"
  .\\.venv\\Scripts\\python.exe tools\\model_tool.py coverage "Orders module"
  .\\.venv\\Scripts\\python.exe tools\\model_tool.py new      "Orders"   (scaffold a new module)
  .\\.venv\\Scripts\\python.exe tools\\model_tool.py list
  .\\.venv\\Scripts\\python.exe tools\\model_tool.py link     "Orders" "Customers" "reason" [basis]
  .\\.venv\\Scripts\\python.exe tools\\model_tool.py components
`link` records that module A depends on module B. It creates B's module folder when missing and
writes both sides to model/dependencies.yaml. Facts about B belong in B's folder, never in A's.
The model lives at "module_explorer/<module folder>/model/<name>.model.yaml". Other generators
(FRS builder, workbook builder, page-object generation) should import load_model().
"""
import re
import sys
from pathlib import Path

import yaml

BASIS = {"Observed", "Verified", "Spec", "Assumption", "Blocked"}
AUTOMATABLE = {"Observed", "Verified"}  # Spec/Assumption/Blocked must be verified first
ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "module_explorer"   # every explored module lives here: module_explorer/<Name> module/


def folder_name(name):
    """'Sales Orders' or 'Sales Orders module' -> 'Sales Orders module'."""
    name = name.strip()
    return name if name.endswith(" module") else f"{name} module"


def short_name(name):
    return folder_name(name)[: -len(" module")]


def load_deps(folder):
    f = MODULES / folder / "model" / "dependencies.yaml"
    if f.exists():
        return yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    return {}


def load_model(folder):
    files = sorted((MODULES / folder / "model").glob("*.model.yaml"))
    if not files:
        sys.exit(f"No *.model.yaml in module_explorer/{folder}/model")
    return yaml.safe_load(files[0].read_text(encoding="utf-8"))


def validate(m):
    errs, warns = [], []
    screens = {s["id"]: s for s in m.get("screens", [])}
    if len(screens) != len(m.get("screens", [])):
        errs.append("duplicate screen ids")
    patterns = set(m.get("patterns", {}))
    for s in m.get("screens", []):
        for k in ("id", "title", "route", "basis"):
            if k not in s:
                errs.append(f"screen {s.get('id', '?')}: missing '{k}'")
        if s.get("basis") not in BASIS:
            errs.append(f"screen {s['id']}: bad basis {s.get('basis')}")
        for p in s.get("pattern", []):
            if p not in patterns:
                errs.append(f"screen {s['id']}: unknown pattern {p}")
        seen = set()
        for f in s.get("fields", []):
            if f.get("id") in seen:
                errs.append(f"screen {s['id']}: duplicate field id {f.get('id')}")
            seen.add(f.get("id"))
            if f.get("basis") not in BASIS:
                errs.append(f"screen {s['id']}.{f.get('id')}: bad basis {f.get('basis')}")
    ids = set()
    for r in m.get("requirements", []):
        if r["id"] in ids:
            errs.append(f"duplicate requirement {r['id']}")
        ids.add(r["id"])
        if r.get("screen") not in screens:
            errs.append(f"{r['id']}: unknown screen {r.get('screen')}")
        if r.get("basis") not in BASIS:
            errs.append(f"{r['id']}: bad basis {r.get('basis')}")
        if not re.fullmatch(r"FR-[A-Z]+-\d{3}", r["id"]):
            warns.append(f"{r['id']}: id does not match FR-<MOD>-nnn")
    used = {r["screen"] for r in m.get("requirements", [])}
    for sid in screens:
        if sid not in used:
            warns.append(f"screen {sid} has no requirement")
    check_code_evidence(m, errs, warns)
    owner = m["module"]["name"]
    for c in m.get("components", []):
        n = c.get("name", "?")
        if c.get("scope") not in ("global", "module"):
            errs.append(f"component {n}: scope must be global or module")
        if c.get("status") not in ("exists", "planned"):
            errs.append(f"component {n}: status must be exists or planned")
        if c.get("scope") == "global" and not c.get("path", "").startswith("components/common/"):
            errs.append(f"component {n}: global components live in components/common/")
        if c.get("scope") == "module" and not c.get("path", "").startswith(f"components/{slug(owner)}/"):
            errs.append(f"component {n}: module components live in components/{slug(owner)}/")
        if c.get("scope") == "global" and len(c.get("used_by", [])) < 2 and c.get("status") == "planned":
            warns.append(f"component {n}: global but used by fewer than 2 modules; keep it module-level until a second module needs it")
        if c.get("scope") == "module" and len(set(c.get("used_by", []))) > 1:
            warns.append(f"component {n}: module-level but used by several modules; promote to components/common/")
        if c.get("status") == "exists" and not (ROOT / c.get("path", "?")).exists():
            errs.append(f"component {n}: path {c.get('path')} does not exist")
    deps = load_deps(folder_name(owner))
    for kind in ("depends_on", "required_by"):
        for d in deps.get(kind, []):
            if not (MODULES / d["module"]).exists():
                errs.append(f"{kind}: module folder missing for {d['module']}")
    return errs, warns


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def check_code_evidence(m, errs, warns):
    """A requirement's optional 'code:' list cites source files: [{file, note}], file relative to module.code_root."""
    root = m["module"].get("code_root")
    root_ok = bool(root) and Path(root).exists()
    for r in m.get("requirements", []):
        for c in r.get("code", []):
            if not c.get("file") or not c.get("note"):
                errs.append(f"{r['id']}: each code item needs 'file' and 'note'")
            elif root_ok and not (Path(root) / c["file"]).exists():
                warns.append(f"{r['id']}: code file not found under code_root: {c['file']}")
    if any(r.get("code") for r in m.get("requirements", [])) and not root:
        warns.append("requirements cite code but module.code_root is not set")


def test_index():
    """Map requirement id -> test files that mention it (marker or comment 'FR-XXX-nnn')."""
    idx = {}
    for f in (ROOT / "tests").rglob("test_*.py") if (ROOT / "tests").exists() else []:
        for rid in set(re.findall(r"FR-[A-Z]+-\d{3}", f.read_text(encoding="utf-8"))):
            idx.setdefault(rid, []).append(f.name)
    return idx


def render(m, folder):
    out = MODULES / folder / "generated"
    out.mkdir(exist_ok=True)
    note = "<!-- GENERATED from model/*.model.yaml - do not edit by hand -->\n"

    # locators.md
    L = [note, f"# {m['module']['name']} locators\n"]
    for name, p in m.get("patterns", {}).items():
        if "locators" in p:
            L.append(f"\n## Pattern: {name}\n| Name | Locator |\n|---|---|")
            L += [f"| {k} | `{v}` |" for k, v in p["locators"].items()]
        if "note" in p:
            L.append(f"\n> {p['note']}")
    for s in m["screens"]:
        L.append(f"\n## {s['title']} (`{s['route']}`)")
        if s.get("locators"):
            L.append("| Name | Locator |\n|---|---|")
            L += [f"| {k} | `{v}` |" for k, v in s["locators"].items()]
        if s.get("fields"):
            L.append("\n| Field | Locator |\n|---|---|")
            for f in s["fields"]:
                L.append(f"| {f['label']} | `{f.get('locator') or '#' + f['id']}` |")
        if s.get("wait"):
            L.append(f"\nWait: {s['wait']}")
    (out / "locators.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # screens.md (FRS-ready field tables)
    S = [note, f"# {m['module']['name']} screens\n"]
    for s in m["screens"]:
        S.append(f"\n## {s['title']}\nRoute `{s['route']}` | Basis: {s['basis']}")
        if s.get("purpose"):
            S.append(f"\n{s['purpose']}")
        if s.get("list"):
            S.append(f"\nColumns: {', '.join(s['list'].get('columns', []))}")
            if s["list"].get("records_seen") is not None:
                S.append(f"\nRecords seen: {s['list']['records_seen']}")
        if s.get("fields"):
            S.append("\n| Label | Id | Type | Default | Mandatory | Editable | Rule | Basis |\n|---|---|---|---|---|---|---|---|")
            for f in s["fields"]:
                S.append("| " + " | ".join(str(f.get(k, "")) for k in
                         ("label", "id", "type", "default", "mandatory", "editable", "rule", "basis")) + " |")
        for d in s.get("discrepancies", []):
            S.append(f"\n- Discrepancy: {d}")
    (out / "screens.md").write_text("\n".join(S) + "\n", encoding="utf-8")

    # traceability.md
    idx = test_index()
    T = [note, "# Requirement traceability\n", "| Requirement | Screen | Basis | Text | Code | Tests |", "|---|---|---|---|---|---|"]
    for r in m["requirements"]:
        tests = sorted(set(r.get("tests", [])) | set(idx.get(r["id"], [])))
        code = ", ".join(Path(c["file"]).name for c in r.get("code", [])) or "-"
        T.append(f"| {r['id']} | {r['screen']} | {r['basis']} | {r['text']} | {code} | {', '.join(tests) or '-'} |")
    T.append("\n## Open questions")
    T += [f"- {q['id']}: {q['text']}" for q in m.get("open_questions", [])]
    (out / "traceability.md").write_text("\n".join(T) + "\n", encoding="utf-8")
    # dependencies.md: links and reusable components
    D = [note, "# Dependencies and components\n"]
    deps = load_deps(folder)
    for kind, title in (("depends_on", "Depends on"), ("required_by", "Required by")):
        D.append(f"\n## {title}")
        D += [f"- **{d['module']}** ({d['basis']}): {d['reason']}" for d in deps.get(kind, [])] or ["- none"]
    D.append("\n## Reusable components\n| Name | Scope | Status | Path | Used by | Notes |\n|---|---|---|---|---|---|")
    for c in m.get("components") or []:
        D.append(f"| {c['name']} | {c['scope']} | {c['status']} | `{c['path']}` | {', '.join(c.get('used_by', []))} | {c.get('note', '')} |")
    (out / "dependencies.md").write_text("\n".join(D) + "\n", encoding="utf-8")
    print(f"Rendered locators.md, screens.md, traceability.md, dependencies.md -> {out}")


def coverage(m):
    idx = test_index()
    rows = {"automatable_no_test": [], "needs_verification": [], "covered": []}
    for r in m["requirements"]:
        has = bool(r.get("tests") or idx.get(r["id"]))
        if has:
            rows["covered"].append(r["id"])
        elif r["basis"] in AUTOMATABLE:
            rows["automatable_no_test"].append(r["id"])
        else:
            rows["needs_verification"].append(f"{r['id']} ({r['basis']})")
    total = len(m["requirements"])
    print(f"Requirements: {total} | covered: {len(rows['covered'])}")
    print("Ready to automate, no test yet:", ", ".join(rows["automatable_no_test"]) or "none")
    print("Blocked until verified (Spec/Assumption/Blocked):", ", ".join(rows["needs_verification"]) or "none")
    coded = [r for r in m["requirements"] if r.get("code")]
    to_observe = [r["id"] for r in coded if r["basis"] not in AUTOMATABLE]
    no_code = [r["id"] for r in m["requirements"] if r["basis"] in AUTOMATABLE and not r.get("code")]
    print(f"Code evidence: {len(coded)} requirements")
    print("Found in code, not yet seen in the UI (verify live next):", ", ".join(to_observe) or "none")
    print("Seen in the UI, no code evidence yet:", ", ".join(no_code) or "none")

SKELETON = """# Module model for {name}. See tools/MODEL_README.md. basis: Observed|Verified|Spec|Assumption|Blocked
module:
  name: {name}
  folder: "{folder}"
  product: ""
  environment: QA
  status: NOT_EXPLORED
  context: {{company: "", plant: ""}}
  sources: []
  menu_root: "{name}"
patterns: {{}}
screens: []
requirements: []
components: []
open_questions: []
test_data: {{prefix: AUTOEXP, note: "Codes only"}}
"""

DEP_SKELETON = {"depends_on": [], "required_by": []}


def write_deps(folder, deps):
    f = MODULES / folder / "model" / "dependencies.yaml"
    f.write_text("# Managed by tools/model_tool.py link. Facts about a linked module live in ITS folder.\n"
                 + yaml.safe_dump(deps, sort_keys=False, allow_unicode=True), encoding="utf-8")


def new_module(name, quiet=False):
    folder = folder_name(name)
    base = MODULES / folder
    if base.exists():
        if not quiet:
            sys.exit(f"{base} already exists")
        return False
    for d in ("model", "screenshots", "exploration"):
        (base / d).mkdir(parents=True)
    n = short_name(name)
    abbr = re.sub(r"[^A-Z]", "", n.upper())[:4] or "MOD"
    (base / "model" / f"{slug(n)}.model.yaml").write_text(
        SKELETON.format(name=n, folder=folder, abbr=abbr), encoding="utf-8")
    write_deps(folder, DEP_SKELETON)
    (base / "exploration" / "created_resources.md").write_text("# Records created by exploration\n", encoding="utf-8")
    print(f"Scaffolded {base}")
    return True


def link(src, dst, reason, basis="Observed"):
    """src depends on dst. Creates dst's folder when missing; records both sides."""
    if basis not in BASIS:
        sys.exit(f"basis must be one of {sorted(BASIS)}")
    a, b = folder_name(src), folder_name(dst)
    if a == b:
        sys.exit("a module cannot depend on itself")
    if not (MODULES / a).exists():
        sys.exit(f"source module {a} does not exist; create it with: new \"{short_name(src)}\"")
    new_module(dst, quiet=True)
    for owner, other, kind in ((a, b, "depends_on"), (b, a, "required_by")):
        deps = load_deps(owner) or {"depends_on": [], "required_by": []}
        deps.setdefault("depends_on", [])
        deps.setdefault("required_by", [])
        if not any(d["module"] == other for d in deps[kind]):
            deps[kind].append({"module": other, "reason": reason, "basis": basis})
        write_deps(owner, deps)
    print(f"Linked: {a} depends on {b} ({basis}): {reason}")


def all_models():
    for d in sorted(MODULES.glob("* module")):
        mf = sorted((d / "model").glob("*.model.yaml"))
        if mf:
            yield d.name, yaml.safe_load(mf[0].read_text(encoding="utf-8"))


def list_modules():
    for name, m in all_models():
        deps = load_deps(name)
        print(f"{name}: {len(m.get('screens') or [])} screens, {len(m.get('requirements') or [])} requirements, "
              f"status {m['module'].get('status')}, depends on {len(deps.get('depends_on', []))}, "
              f"required by {len(deps.get('required_by', []))}")


def components_report():
    rows = {}
    for name, m in all_models():
        for c in m.get("components") or []:
            r = rows.setdefault(c["name"], {"scope": c["scope"], "path": c["path"], "status": c["status"], "mods": set()})
            r["mods"].update(c.get("used_by", []) or [short_name(name)])
    for n, r in sorted(rows.items(), key=lambda x: (x[1]["scope"], x[0])):
        flag = ""
        if r["scope"] == "module" and len(r["mods"]) > 1:
            flag = "  <- PROMOTE to components/common/"
        print(f"{r['scope']:6} {r['status']:8} {n:24} {r['path']}  used by: {', '.join(sorted(r['mods']))}{flag}")


def main():
    a = sys.argv[1:]
    if a[:1] == ["list"] and len(a) == 1:
        return list_modules()
    if a[:1] == ["components"] and len(a) == 1:
        return components_report()
    if a[:1] == ["link"] and len(a) in (4, 5):
        return link(*a[1:])
    if len(a) != 2 or a[0] not in ("validate", "render", "coverage", "new"):
        sys.exit(__doc__)
    cmd, folder = a
    if cmd == "new":
        return new_module(folder)
    folder = folder_name(folder)
    m = load_model(folder)
    errs, warns = validate(m)
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)
    if errs:
        sys.exit(1)
    if cmd == "validate":
        print(f"OK: {len(m.get('screens') or [])} screens, {len(m.get('requirements') or [])} requirements")
    elif cmd == "render":
        render(m, folder)
    else:
        coverage(m)


if __name__ == "__main__":
    main()
