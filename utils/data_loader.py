import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"


def load(name: str) -> dict:
    """Load test_data/<name>.json (e.g. load("orders/master"))."""
    return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
