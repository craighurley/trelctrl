import httpx
import pytest
import respx

from trelctl.trello.labels import COLOURS, get_labels, pick_colour

BASE = "https://api.trello.com/1"
BOARD_ID = "board123"


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLO_API_KEY", "test-key")
    monkeypatch.setenv("TRELLO_TOKEN", "test-token")


@respx.mock
def test_get_labels_returns_list() -> None:
    labels_data = [
        {"id": "lbl1", "name": "Bug"},
        {"id": "lbl2", "name": "Feature"},
    ]
    respx.get(f"{BASE}/boards/{BOARD_ID}/labels").mock(
        return_value=httpx.Response(200, json=labels_data)
    )
    result = get_labels(BOARD_ID)
    assert result == labels_data


@respx.mock
def test_get_labels_empty_board() -> None:
    respx.get(f"{BASE}/boards/{BOARD_ID}/labels").mock(return_value=httpx.Response(200, json=[]))
    result = get_labels(BOARD_ID)
    assert result == []


def test_pick_colour_no_used() -> None:
    colour = pick_colour([])
    assert colour in COLOURS


def test_pick_colour_avoids_used() -> None:
    used = ["yellow", "purple", "blue", "red", "green", "orange", "black", "sky", "pink"]
    for _ in range(20):
        assert pick_colour(used) == "lime"


def test_pick_colour_all_used_still_returns_valid() -> None:
    colour = pick_colour(list(COLOURS))
    assert colour in COLOURS
