import csv
from datetime import date
from typing import Optional
from dateutil import parser as dateutil_parser
from gbgolf.data.models import Card

REQUIRED_ROSTER_COLUMNS = {
    "Player", "Multiplier", "Salary", "Collection", "Expires",
    "Franchise", "Rookie"
}


def _parse_expires(raw: str) -> Optional[date]:
    """Parse Expires column. Blank or unparseable = None (never expires, card is valid)."""
    raw = raw.strip()
    if not raw:
        return None
    # Try ISO format first (fast path)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass
    # Fallback to dateutil for formats like "Mar 15, 2026" or "3/15/2026"
    try:
        return dateutil_parser.parse(raw, dayfirst=False).date()
    except Exception:
        # Log and treat as no expiry — safer to include than silently exclude
        import warnings
        warnings.warn(f"Could not parse Expires value: {raw!r} — treating as no expiry")
        return None


def _row_to_card(row: dict, instance_id: int) -> Card:
    salary_raw = row.get("Salary", "0").strip()
    salary = int(float(salary_raw)) if salary_raw else 0
    multiplier_raw = row.get("Multiplier", "1.0").strip()
    multiplier = float(multiplier_raw) if multiplier_raw else 1.0
    expires = _parse_expires(row.get("Expires", ""))
    return Card(
        player=row["Player"].strip(),
        salary=salary,
        multiplier=multiplier,
        collection=row.get("Collection", "").strip(),
        expires=expires,
        instance_id=instance_id,
        franchise=row.get("Franchise", "").strip(),
        rookie=row.get("Rookie", "").strip(),
    )


def parse_roster_csv(path: str) -> list[Card]:
    """Parse GameBlazers roster CSV. Raises ValueError on missing required columns.

    Each card receives a unique ``instance_id`` derived from its row index, so
    the optimizer can distinguish duplicate rows (same player+salary+multiplier
    +collection) representing multiple owned copies of one card.
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"Roster CSV is empty or unreadable: {path}")
        missing = REQUIRED_ROSTER_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Roster CSV missing required columns: {sorted(missing)}"
            )
        return [_row_to_card(row, instance_id=idx) for idx, row in enumerate(reader)]
