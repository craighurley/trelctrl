from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from trelctl.commands.create_board import app as create_board_app
from trelctl.commands.delete_cards import app as delete_cards_app
from trelctl.commands.delete_labels import app as delete_labels_app
from trelctl.commands.delete_lists import app as delete_lists_app
from trelctl.commands.get_cards import _FIELDS, _format_card
from trelctl.commands.get_cards import app as get_cards_app
from trelctl.commands.get_lists import app as get_lists_app
from trelctl.commands.get_members import app as get_members_app
from trelctl.commands.import_cards import app as import_cards_app
from trelctl.commands.import_lists import app as import_lists_app

BASE = "https://api.trello.com/1"
runner = CliRunner()


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLO_API_KEY", "test-key")
    monkeypatch.setenv("TRELLO_TOKEN", "test-token")


def _boards_mock() -> list[dict]:
    return [{"id": "board1", "name": "My Board"}]


def _lists_mock() -> list[dict]:
    return [{"id": "list1", "name": "Backlog"}]


# --- create board ---


@respx.mock
def test_create_board_prints_result() -> None:
    respx.post(f"{BASE}/boards").mock(
        return_value=httpx.Response(200, json={"id": "abc123", "name": "My Board"})
    )
    result = runner.invoke(create_board_app, ["My Board"])
    assert result.exit_code == 0
    assert 'Created board: "My Board" (id: abc123)' in result.output


# --- get lists ---


@respx.mock
def test_get_lists_writes_csv() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=_lists_mock())
    )
    result = runner.invoke(get_lists_app, ["--board", "My Board"])
    assert result.exit_code == 0
    assert "name\n" in result.output
    assert "Backlog" in result.output


@respx.mock
def test_get_lists_empty_board() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(return_value=httpx.Response(200, json=[]))
    result = runner.invoke(get_lists_app, ["--board", "My Board"])
    assert result.exit_code == 0
    assert "name" in result.output


# --- get members ---


@respx.mock
def test_get_members_writes_csv() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/members").mock(
        return_value=httpx.Response(200, json=[{"id": "mem1"}, {"id": "mem2"}])
    )
    result = runner.invoke(get_members_app, ["--board", "My Board"])
    assert result.exit_code == 0
    assert "name\n" in result.output
    assert "mem1" in result.output
    assert "mem2" in result.output


# --- get cards ---


def test_fields_match_import_columns() -> None:
    """Round-trip: get_cards CSV columns must match import_cards columns."""
    expected = ["name", "description", "labels", "due_date", "checklist", "members"]
    assert _FIELDS == expected


def test_format_card_basic() -> None:
    card = {
        "id": "card1",
        "name": "Fix bug",
        "desc": "Steps to reproduce",
        "labels": [{"name": "Bug"}, {"name": "High Priority"}],
        "due": "2026-04-15T00:00:00.000Z",
        "idMembers": ["abc123", "def456"],
        "badges": {"checkItems": 0},
    }
    result = _format_card(card)
    assert result["name"] == "Fix bug"
    assert result["description"] == "Steps to reproduce"
    assert result["labels"] == "Bug|High Priority"
    assert result["due_date"] == "2026-04-15"
    assert result["members"] == "abc123|def456"
    assert result["checklist"] == ""


def test_format_card_no_optional_fields() -> None:
    card = {
        "id": "card1",
        "name": "Simple card",
        "desc": "",
        "labels": [],
        "due": None,
        "idMembers": [],
        "badges": {"checkItems": 0},
    }
    result = _format_card(card)
    assert result["description"] == ""
    assert result["labels"] == ""
    assert result["due_date"] == ""
    assert result["members"] == ""
    assert result["checklist"] == ""


def test_format_card_returns_all_fields() -> None:
    card = {
        "id": "card1",
        "name": "Test",
        "desc": "",
        "labels": [],
        "due": None,
        "idMembers": [],
        "badges": {"checkItems": 0},
    }
    result = _format_card(card)
    assert set(result.keys()) == set(_FIELDS)


def test_format_card_due_date_extraction() -> None:
    card = {
        "id": "card1",
        "name": "Test",
        "desc": "",
        "labels": [],
        "due": "2026-12-31T12:30:00.000Z",
        "idMembers": [],
        "badges": {"checkItems": 0},
    }
    result = _format_card(card)
    assert result["due_date"] == "2026-12-31"


@respx.mock
def test_format_card_with_checklists() -> None:
    checklists = [
        {"checkItems": [{"name": "Write tests"}, {"name": "Review PR"}]},
        {"checkItems": [{"name": "Deploy"}]},
    ]
    respx.get(f"{BASE}/cards/card1/checklists").mock(
        return_value=httpx.Response(200, json=checklists)
    )
    card = {
        "id": "card1",
        "name": "Task with checklist",
        "desc": "",
        "labels": [],
        "due": None,
        "idMembers": [],
        "badges": {"checkItems": 3},
    }
    result = _format_card(card)
    assert result["checklist"] == "Write tests|Review PR|Deploy"


@respx.mock
def test_get_cards_writes_csv() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/cards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "c1",
                    "name": "Fix bug",
                    "desc": "",
                    "labels": [],
                    "due": None,
                    "idMembers": [],
                    "badges": {"checkItems": 0},
                }
            ],
        )
    )
    result = runner.invoke(get_cards_app, ["--board", "My Board"])
    assert result.exit_code == 0
    assert "Fix bug" in result.output
    assert "name" in result.output


@respx.mock
def test_get_cards_filtered_by_list() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=_lists_mock())
    )
    respx.get(f"{BASE}/lists/list1/cards").mock(return_value=httpx.Response(200, json=[]))
    result = runner.invoke(get_cards_app, ["--board", "My Board", "--list", "Backlog"])
    assert result.exit_code == 0
    assert "name" in result.output


# --- import lists ---


@respx.mock
def test_import_lists_creates_lists(tmp_path: Path) -> None:
    csv = tmp_path / "lists.csv"
    csv.write_text("name\nBacklog\nDone\n")
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.post(f"{BASE}/boards/board1/lists").mock(
        side_effect=[
            httpx.Response(200, json={"id": "l1", "name": "Backlog"}),
            httpx.Response(200, json={"id": "l2", "name": "Done"}),
        ]
    )
    result = runner.invoke(import_lists_app, ["--board", "My Board", str(csv)])
    assert result.exit_code == 0
    assert 'Created list: "Backlog"' in result.output
    assert 'Created list: "Done"' in result.output
    assert "Done. Created 2 list(s)." in result.output


@respx.mock
def test_import_lists_dry_run(tmp_path: Path) -> None:
    csv = tmp_path / "lists.csv"
    csv.write_text("name\nBacklog\n")
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    result = runner.invoke(import_lists_app, ["--board", "My Board", "--dry-run", str(csv)])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "Backlog" in result.output
    # No POST to lists should have been made
    assert not any(
        str(r.request.url).endswith("/lists") and r.request.method == "POST" for r in respx.calls
    )


# --- import cards ---


@respx.mock
def test_import_cards_creates_card(tmp_path: Path) -> None:
    csv = tmp_path / "cards.csv"
    csv.write_text("name\nFix bug\n")
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=_lists_mock())
    )
    respx.post(f"{BASE}/cards").mock(
        return_value=httpx.Response(200, json={"id": "card1", "name": "Fix bug"})
    )
    result = runner.invoke(import_cards_app, ["--board", "My Board", "--list", "Backlog", str(csv)])
    assert result.exit_code == 0
    assert 'Created card: "Fix bug"' in result.output
    assert "Done. Created 1 card(s)." in result.output


@respx.mock
def test_import_cards_creates_card_with_checklist(tmp_path: Path) -> None:
    csv = tmp_path / "cards.csv"
    csv.write_text("name,checklist\nFix bug,Step 1|Step 2\n")
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=_lists_mock())
    )
    respx.post(f"{BASE}/cards").mock(
        return_value=httpx.Response(200, json={"id": "card1", "name": "Fix bug"})
    )
    respx.post(f"{BASE}/cards/card1/checklists").mock(
        return_value=httpx.Response(200, json={"id": "cl1"})
    )
    respx.post(f"{BASE}/checklists/cl1/checkItems").mock(
        return_value=httpx.Response(200, json={"id": "ci1"})
    )
    result = runner.invoke(import_cards_app, ["--board", "My Board", "--list", "Backlog", str(csv)])
    assert result.exit_code == 0
    assert 'Created card: "Fix bug"' in result.output


@respx.mock
def test_import_cards_dry_run(tmp_path: Path) -> None:
    csv = tmp_path / "cards.csv"
    csv.write_text("name\nFix bug\n")
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=_lists_mock())
    )
    result = runner.invoke(
        import_cards_app, ["--board", "My Board", "--list", "Backlog", "--dry-run", str(csv)]
    )
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert "Fix bug" in result.output
    assert "Done. Would create 1 card(s)." in result.output


@respx.mock
def test_import_cards_creates_missing_label(tmp_path: Path) -> None:
    csv = tmp_path / "cards.csv"
    csv.write_text("name,labels\nFix bug,Ghost\n")
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=_lists_mock())
    )
    respx.get(f"{BASE}/boards/board1/labels").mock(
        return_value=httpx.Response(200, json=[{"id": "lbl1", "name": "Bug"}])
    )
    respx.post(f"{BASE}/boards/board1/labels").mock(
        return_value=httpx.Response(200, json={"id": "lbl2", "name": "Ghost"})
    )
    respx.post(f"{BASE}/cards").mock(
        return_value=httpx.Response(200, json={"id": "card1", "name": "Fix bug"})
    )
    result = runner.invoke(import_cards_app, ["--board", "My Board", "--list", "Backlog", str(csv)])
    assert result.exit_code == 0
    assert 'Created label: "Ghost" (id: lbl2)' in result.output
    assert 'Created card: "Fix bug"' in result.output
    # Verify the card was posted with the newly created label ID
    post_call = next(
        c
        for c in respx.calls
        if c.request.method == "POST"
        and "/cards" in str(c.request.url)
        and "/labels" not in str(c.request.url)
    )
    assert "lbl2" in str(post_call.request.url)


@respx.mock
def test_import_cards_resolves_labels(tmp_path: Path) -> None:
    csv = tmp_path / "cards.csv"
    csv.write_text("name,labels\nFix bug,Bug\n")
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=_lists_mock())
    )
    respx.get(f"{BASE}/boards/board1/labels").mock(
        return_value=httpx.Response(200, json=[{"id": "lbl1", "name": "Bug"}])
    )
    respx.post(f"{BASE}/cards").mock(
        return_value=httpx.Response(200, json={"id": "card1", "name": "Fix bug"})
    )
    result = runner.invoke(import_cards_app, ["--board", "My Board", "--list", "Backlog", str(csv)])
    assert result.exit_code == 0
    assert 'Created card: "Fix bug"' in result.output
    # Verify the card was posted with the resolved label ID
    post_call = next(
        c
        for c in respx.calls
        if c.request.method == "POST"
        and "/cards" in str(c.request.url)
        and "/checklists" not in str(c.request.url)
    )
    assert "lbl1" in str(post_call.request.url)


# --- delete labels ---


@respx.mock
def test_delete_labels_deletes_all() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/labels").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "lbl1", "name": "Bug"},
                {"id": "lbl2", "name": "Feature"},
            ],
        )
    )
    respx.delete(f"{BASE}/labels/lbl1").mock(return_value=httpx.Response(200, json={}))
    respx.delete(f"{BASE}/labels/lbl2").mock(return_value=httpx.Response(200, json={}))
    result = runner.invoke(delete_labels_app, ["--board", "My Board", "--yes"])
    assert result.exit_code == 0
    assert 'Deleted label: "Bug" (id: lbl1)' in result.output
    assert 'Deleted label: "Feature" (id: lbl2)' in result.output
    assert "Done. Deleted 2 label(s)." in result.output


@respx.mock
def test_delete_labels_empty_board() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/labels").mock(return_value=httpx.Response(200, json=[]))
    result = runner.invoke(delete_labels_app, ["--board", "My Board"])
    assert result.exit_code == 0
    assert "No labels found on board." in result.output


# --- delete cards ---


@respx.mock
def test_delete_cards_deletes_all() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/cards").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "c1", "name": "Fix bug"},
                {"id": "c2", "name": "Add feature"},
            ],
        )
    )
    respx.delete(f"{BASE}/cards/c1").mock(return_value=httpx.Response(200, json={}))
    respx.delete(f"{BASE}/cards/c2").mock(return_value=httpx.Response(200, json={}))
    result = runner.invoke(delete_cards_app, ["--board", "My Board", "--yes"])
    assert result.exit_code == 0
    assert 'Deleted card: "Fix bug" (id: c1)' in result.output
    assert 'Deleted card: "Add feature" (id: c2)' in result.output
    assert "Done. Deleted 2 card(s)." in result.output


@respx.mock
def test_delete_cards_empty_board() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/cards").mock(return_value=httpx.Response(200, json=[]))
    result = runner.invoke(delete_cards_app, ["--board", "My Board"])
    assert result.exit_code == 0
    assert "No cards found on board." in result.output


# --- delete lists ---


@respx.mock
def test_delete_lists_archives_all() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "list1", "name": "Backlog"},
                {"id": "list2", "name": "Done"},
            ],
        )
    )
    respx.put(f"{BASE}/lists/list1/closed").mock(
        return_value=httpx.Response(200, json={"id": "list1", "closed": True})
    )
    respx.put(f"{BASE}/lists/list2/closed").mock(
        return_value=httpx.Response(200, json={"id": "list2", "closed": True})
    )
    result = runner.invoke(delete_lists_app, ["--board", "My Board", "--yes"])
    assert result.exit_code == 0
    assert 'Archived list: "Backlog" (id: list1)' in result.output
    assert 'Archived list: "Done" (id: list2)' in result.output
    assert "Done. Archived 2 list(s)." in result.output


@respx.mock
def test_delete_lists_empty_board() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(return_value=httpx.Response(200, json=[]))
    result = runner.invoke(delete_lists_app, ["--board", "My Board"])
    assert result.exit_code == 0
    assert "No lists found on board." in result.output


# --- delete confirmation prompts ---


@respx.mock
def test_delete_labels_aborts_on_no() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/labels").mock(
        return_value=httpx.Response(200, json=[{"id": "lbl1", "name": "Bug"}])
    )
    result = runner.invoke(delete_labels_app, ["--board", "My Board"], input="n\n")
    assert result.exit_code == 1
    assert "Deleted label" not in result.output


@respx.mock
def test_delete_cards_aborts_on_no() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/cards").mock(
        return_value=httpx.Response(200, json=[{"id": "c1", "name": "Fix bug"}])
    )
    result = runner.invoke(delete_cards_app, ["--board", "My Board"], input="n\n")
    assert result.exit_code == 1
    assert "Deleted card" not in result.output


@respx.mock
def test_delete_lists_aborts_on_no() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(
        return_value=httpx.Response(200, json=_boards_mock())
    )
    respx.get(f"{BASE}/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=[{"id": "list1", "name": "Backlog"}])
    )
    result = runner.invoke(delete_lists_app, ["--board", "My Board"], input="n\n")
    assert result.exit_code == 1
    assert "Archived list" not in result.output
