"""Unique test-data generators (timestamp based) so tests stay independent and re-runnable."""
from datetime import datetime


def stamp() -> str:
    """Timestamp suffix, e.g. 20261019143005."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def unique_name(prefix: str = "AUTO") -> str:
    """Readable unique name, e.g. AUTO_20261019143005."""
    return f"{prefix}_{stamp()}"


def unique_number(digits: int = 8) -> int:
    """Numeric key of at most `digits` digits, derived from the clock."""
    return int(datetime.now().strftime("%d%H%M%S%f")[:digits])
