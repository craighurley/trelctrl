import httpx
import pytest
import respx

from trelctl.trello.boards import create_board, resolve_board

BASE = "https://api.trello.com/1"


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLO_API_KEY", "test-key")
    monkeypatch.setenv("TRELLO_TOKEN", "test-token")


BOARDS = [
    {"id": "board1", "name": "My Board"},
    {"id": "board2", "name": "Another Board"},
]


# --- resolve_board ---


@respx.mock
def test_resolve_board_by_name() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(return_value=httpx.Response(200, json=BOARDS))
    result = resolve_board("My Board")
    assert result["id"] == "board1"


@respx.mock
def test_resolve_board_by_name_case_insensitive() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(return_value=httpx.Response(200, json=BOARDS))
    result = resolve_board("my board")
    assert result["id"] == "board1"


@respx.mock
def test_resolve_board_by_id() -> None:
    respx.get(f"{BASE}/members/me/boards").mock(return_value=httpx.Response(200, json=BOARDS))
    result = resolve_board("board2")
    assert result["name"] == "Another Board"


@respx.mock
def test_resolve_board_name_takes_priority_over_id() -> None:
    boards = [
        {"id": "board1", "name": "board2"},  # name matches "board2" string
        {"id": "board2", "name": "Another Board"},
    ]
    respx.get(f"{BASE}/members/me/boards").mock(return_value=httpx.Response(200, json=boards))
    result = resolve_board("board2")
    assert result["id"] == "board1"


@respx.mock
def test_resolve_board_not_found_exits(capsys: pytest.CaptureFixture) -> None:
    respx.get(f"{BASE}/members/me/boards").mock(return_value=httpx.Response(200, json=BOARDS))
    with pytest.raises(SystemExit) as exc:
        resolve_board("Ghost Board")
    assert exc.value.code == 1
    assert "Ghost Board" in capsys.readouterr().err


# --- create_board ---


@respx.mock
def test_create_board_returns_board() -> None:
    respx.post(f"{BASE}/boards").mock(
        return_value=httpx.Response(200, json={"id": "newboard", "name": "New Board"})
    )
    result = create_board("New Board")
    assert result["id"] == "newboard"
    assert result["name"] == "New Board"
