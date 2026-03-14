import httpx
import pytest
import respx

from trelctl.trello.labels import get_labels, resolve_label_ids

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
def test_resolve_label_ids_matches_by_name() -> None:
    labels_data = [
        {"id": "lbl1", "name": "Bug"},
        {"id": "lbl2", "name": "Feature"},
    ]
    respx.get(f"{BASE}/boards/{BOARD_ID}/labels").mock(
        return_value=httpx.Response(200, json=labels_data)
    )
    result = resolve_label_ids(BOARD_ID, ["Bug", "Feature"])
    assert result == ["lbl1", "lbl2"]


@respx.mock
def test_resolve_label_ids_case_insensitive() -> None:
    labels_data = [{"id": "lbl1", "name": "Bug"}]
    respx.get(f"{BASE}/boards/{BOARD_ID}/labels").mock(
        return_value=httpx.Response(200, json=labels_data)
    )
    result = resolve_label_ids(BOARD_ID, ["bug", "BUG"])
    assert result == ["lbl1", "lbl1"]


@respx.mock
def test_resolve_label_ids_warns_and_skips_unknown(capsys: pytest.CaptureFixture) -> None:
    labels_data = [{"id": "lbl1", "name": "Bug"}]
    respx.get(f"{BASE}/boards/{BOARD_ID}/labels").mock(
        return_value=httpx.Response(200, json=labels_data)
    )
    result = resolve_label_ids(BOARD_ID, ["Bug", "NonExistent"])
    assert result == ["lbl1"]
    assert "NonExistent" in capsys.readouterr().err


@respx.mock
def test_resolve_label_ids_empty_input() -> None:
    respx.get(f"{BASE}/boards/{BOARD_ID}/labels").mock(return_value=httpx.Response(200, json=[]))
    result = resolve_label_ids(BOARD_ID, [])
    assert result == []
    # No API call should be made for empty input
    assert not respx.calls


@respx.mock
def test_resolve_label_ids_all_unknown_returns_empty(capsys: pytest.CaptureFixture) -> None:
    labels_data = [{"id": "lbl1", "name": "Bug"}]
    respx.get(f"{BASE}/boards/{BOARD_ID}/labels").mock(
        return_value=httpx.Response(200, json=labels_data)
    )
    result = resolve_label_ids(BOARD_ID, ["Ghost", "Phantom"])
    assert result == []
    stderr = capsys.readouterr().err
    assert "Ghost" in stderr
    assert "Phantom" in stderr
