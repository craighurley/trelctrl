from pathlib import Path

import pytest

from trelctl.parser import parse_cards, parse_lists

# --- Helpers ---


def _csv_file(content: str, tmp_path: Path) -> Path:
    f = tmp_path / "data.csv"
    f.write_text(content, encoding="utf-8")
    return f


# --- parse_lists ---


def test_parse_lists_returns_names(tmp_path: Path) -> None:
    f = _csv_file("name\nBacklog\nIn Progress\nDone\n", tmp_path)
    result = parse_lists(f)
    assert result == ["Backlog", "In Progress", "Done"]


def test_parse_lists_skips_empty_names(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    # Use an explicitly quoted empty string — DictReader silently skips fully blank lines
    f = _csv_file('name\nBacklog\n""\nDone\n', tmp_path)
    result = parse_lists(f)
    assert result == ["Backlog", "Done"]
    stderr = capsys.readouterr().err
    assert "empty name" in stderr


def test_parse_lists_empty_file(tmp_path: Path) -> None:
    f = _csv_file("name\n", tmp_path)
    assert parse_lists(f) == []


# --- parse_cards ---


def test_parse_cards_minimal(tmp_path: Path) -> None:
    f = _csv_file("name\nFix bug\n", tmp_path)
    rows = parse_cards(f)
    assert len(rows) == 1
    assert rows[0].name == "Fix bug"
    assert rows[0].description == ""
    assert rows[0].labels == []
    assert rows[0].due_date == ""
    assert rows[0].checklist == []
    assert rows[0].members == []


def test_parse_cards_all_fields(tmp_path: Path) -> None:
    csv_content = (
        "name,description,labels,due_date,checklist,members\n"
        '"Fix bug","Steps to reproduce","Bug,High Priority",'
        '"2026-04-15","Write tests|Review PR|Deploy","abc123|def456"\n'
    )
    f = _csv_file(csv_content, tmp_path)
    rows = parse_cards(f)
    assert len(rows) == 1
    row = rows[0]
    assert row.name == "Fix bug"
    assert row.labels == ["Bug", "High Priority"]
    assert row.checklist == ["Write tests", "Review PR", "Deploy"]
    assert row.members == ["abc123", "def456"]


def test_parse_cards_skips_empty_name(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    f = _csv_file('name\nFix bug\n""\nAnother\n', tmp_path)
    rows = parse_cards(f)
    assert len(rows) == 2
    assert rows[0].name == "Fix bug"
    assert rows[1].name == "Another"
    assert "empty name" in capsys.readouterr().err


def test_parse_cards_invalid_due_date_exits(tmp_path: Path) -> None:
    f = _csv_file("name,due_date\nFix bug,15-04-2026\n", tmp_path)
    with pytest.raises(SystemExit) as exc:
        parse_cards(f)
    assert exc.value.code == 1


def test_parse_cards_valid_due_date(tmp_path: Path) -> None:
    f = _csv_file("name,due_date\nFix bug,2026-04-15\n", tmp_path)
    rows = parse_cards(f)
    assert rows[0].due_date == "2026-04-15"


def test_parse_cards_column_order_independent(tmp_path: Path) -> None:
    f = _csv_file("checklist,name,labels\nStep1|Step2,My card,Bug\n", tmp_path)
    rows = parse_cards(f)
    assert rows[0].name == "My card"
    assert rows[0].labels == ["Bug"]
    assert rows[0].checklist == ["Step1", "Step2"]


def test_parse_cards_empty_optional_fields(tmp_path: Path) -> None:
    f = _csv_file("name,labels,checklist,members\nFix bug,,,\n", tmp_path)
    rows = parse_cards(f)
    assert rows[0].labels == []
    assert rows[0].checklist == []
    assert rows[0].members == []
