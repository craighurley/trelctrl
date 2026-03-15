import csv
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class CardRow:
    name: str
    description: str = ""
    labels: list[str] = field(default_factory=list)
    due_date: str = ""
    checklist: list[str] = field(default_factory=list)
    members: list[str] = field(default_factory=list)


def parse_lists(path: Path) -> list[str]:
    """Parse a lists CSV and return a list of names.

    Rows with an empty name are skipped with a warning to stderr.
    """
    names: list[str] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # row 1 is header
            name = row.get("name", "").strip()
            if not name:
                print(f"Warning: row {i} has an empty name — skipping.", file=sys.stderr)
                continue
            names.append(name)
    return names


def parse_cards(path: Path) -> list[CardRow]:
    """Parse a cards CSV and return a list of CardRow dataclasses.

    Rows with an empty name are skipped with a warning to stderr.
    Invalid due_date formats are rejected with an error to stderr (exits non-zero).
    """
    rows: list[CardRow] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            name = row.get("name", "").strip()
            if not name:
                print(f"Warning: row {i} has an empty name — skipping.", file=sys.stderr)
                continue

            due_date = row.get("due_date", "").strip()
            if due_date:
                try:
                    datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    print(
                        f"Error: row {i} has invalid due_date '{due_date}' (expected YYYY-MM-DD).",
                        file=sys.stderr,
                    )
                    raise SystemExit(1)

            labels_raw = row.get("labels", "").strip()
            labels = (
                [lbl.strip() for lbl in labels_raw.split("|") if lbl.strip()] if labels_raw else []
            )

            checklist_raw = row.get("checklist", "").strip()
            checklist = (
                [item.strip() for item in checklist_raw.split("|") if item.strip()]
                if checklist_raw
                else []
            )

            members_raw = row.get("members", "").strip()
            members = (
                [m.strip() for m in members_raw.split("|") if m.strip()] if members_raw else []
            )

            rows.append(
                CardRow(
                    name=name,
                    description=row.get("description", "").strip(),
                    labels=labels,
                    due_date=due_date,
                    checklist=checklist,
                    members=members,
                )
            )
    return rows


def due_date_to_rfc3339(due_date: str) -> str:
    """Convert YYYY-MM-DD to RFC3339 datetime string (midnight UTC)."""
    return f"{due_date}T00:00:00.000Z"
