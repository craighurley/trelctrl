import httpx
import pytest
import respx

from trelctl.trello.lists import create_list, get_lists, resolve_list

BASE = "https://api.trello.com/1"
BOARD_ID = "board123"


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLO_API_KEY", "test-key")
    monkeypatch.setenv("TRELLO_TOKEN", "test-token")


LISTS = [
    {"id": "list1", "name": "Backlog"},
    {"id": "list2", "name": "In Progress"},
]


# --- get_lists ---


@respx.mock
def test_get_lists_returns_list() -> None:
    respx.get(f"{BASE}/boards/{BOARD_ID}/lists").mock(return_value=httpx.Response(200, json=LISTS))
    result = get_lists(BOARD_ID)
    assert result == LISTS


# --- resolve_list ---


@respx.mock
def test_resolve_list_by_name() -> None:
    respx.get(f"{BASE}/boards/{BOARD_ID}/lists").mock(return_value=httpx.Response(200, json=LISTS))
    result = resolve_list(BOARD_ID, "Backlog")
    assert result["id"] == "list1"


@respx.mock
def test_resolve_list_by_name_case_insensitive() -> None:
    respx.get(f"{BASE}/boards/{BOARD_ID}/lists").mock(return_value=httpx.Response(200, json=LISTS))
    result = resolve_list(BOARD_ID, "backlog")
    assert result["id"] == "list1"


@respx.mock
def test_resolve_list_by_id() -> None:
    respx.get(f"{BASE}/boards/{BOARD_ID}/lists").mock(return_value=httpx.Response(200, json=LISTS))
    result = resolve_list(BOARD_ID, "list2")
    assert result["name"] == "In Progress"


@respx.mock
def test_resolve_list_not_found_exits(capsys: pytest.CaptureFixture) -> None:
    respx.get(f"{BASE}/boards/{BOARD_ID}/lists").mock(return_value=httpx.Response(200, json=LISTS))
    with pytest.raises(SystemExit) as exc:
        resolve_list(BOARD_ID, "Does Not Exist")
    assert exc.value.code == 1
    assert "Does Not Exist" in capsys.readouterr().err


# --- create_list ---


@respx.mock
def test_create_list_returns_list() -> None:
    respx.post(f"{BASE}/boards/{BOARD_ID}/lists").mock(
        return_value=httpx.Response(200, json={"id": "newlist", "name": "Done"})
    )
    result = create_list(BOARD_ID, "Done")
    assert result["id"] == "newlist"
    assert result["name"] == "Done"
