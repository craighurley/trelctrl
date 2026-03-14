import httpx
import pytest
import respx

from trelctl.trello import client

BASE = "https://api.trello.com/1"


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLO_API_KEY", "test-key")
    monkeypatch.setenv("TRELLO_TOKEN", "test-token")


# --- get_auth ---


def test_get_auth_returns_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRELLO_API_KEY", "mykey")
    monkeypatch.setenv("TRELLO_TOKEN", "mytoken")
    auth = client.get_auth()
    assert auth == {"key": "mykey", "token": "mytoken"}


def test_get_auth_missing_api_key_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.delenv("TRELLO_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        client.get_auth()
    assert exc.value.code == 1
    assert "TRELLO_API_KEY" in capsys.readouterr().err


def test_get_auth_missing_token_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.delenv("TRELLO_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        client.get_auth()
    assert exc.value.code == 1
    assert "TRELLO_TOKEN" in capsys.readouterr().err


def test_get_auth_missing_both_lists_both(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.delenv("TRELLO_API_KEY", raising=False)
    monkeypatch.delenv("TRELLO_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        client.get_auth()
    err = capsys.readouterr().err
    assert "TRELLO_API_KEY" in err
    assert "TRELLO_TOKEN" in err


# --- get ---


@respx.mock
def test_get_returns_json() -> None:
    respx.get(f"{BASE}/some/path").mock(return_value=httpx.Response(200, json={"ok": True}))
    result = client.get("/some/path")
    assert result == {"ok": True}


@respx.mock
def test_get_includes_auth_params() -> None:
    route = respx.get(f"{BASE}/some/path").mock(return_value=httpx.Response(200, json={}))
    client.get("/some/path")
    request = route.calls[0].request
    assert "key=test-key" in str(request.url)
    assert "token=test-token" in str(request.url)


@respx.mock
def test_get_error_response_exits(capsys: pytest.CaptureFixture) -> None:
    respx.get(f"{BASE}/bad/path").mock(return_value=httpx.Response(404, text="Not Found"))
    with pytest.raises(SystemExit) as exc:
        client.get("/bad/path")
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "404" in err


# --- post ---


@respx.mock
def test_post_returns_json() -> None:
    respx.post(f"{BASE}/some/path").mock(return_value=httpx.Response(200, json={"id": "abc"}))
    result = client.post("/some/path", {"name": "Test"})
    assert result == {"id": "abc"}


@respx.mock
def test_post_includes_auth_params() -> None:
    route = respx.post(f"{BASE}/some/path").mock(return_value=httpx.Response(200, json={}))
    client.post("/some/path", {"name": "Test"})
    request = route.calls[0].request
    assert "key=test-key" in str(request.url)
    assert "token=test-token" in str(request.url)


@respx.mock
def test_post_error_response_exits(capsys: pytest.CaptureFixture) -> None:
    respx.post(f"{BASE}/bad/path").mock(return_value=httpx.Response(400, text="Bad Request"))
    with pytest.raises(SystemExit) as exc:
        client.post("/bad/path")
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "400" in err
