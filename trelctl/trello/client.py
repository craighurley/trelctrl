import logging
import os
import sys
from typing import Any

import httpx

BASE_URL = "https://api.trello.com/1"

logger = logging.getLogger(__name__)


def get_auth() -> dict[str, str]:
    """Read and validate Trello credentials from environment variables."""
    api_key = os.environ.get("TRELLO_API_KEY", "")
    token = os.environ.get("TRELLO_TOKEN", "")

    missing = []
    if not api_key:
        missing.append("TRELLO_API_KEY")
    if not token:
        missing.append("TRELLO_TOKEN")

    if missing:
        vars_list = ", ".join(missing)
        print(f"Error: missing required environment variable(s): {vars_list}", file=sys.stderr)
        raise SystemExit(1)

    return {"key": api_key, "token": token}


def get(path: str, params: dict | None = None) -> Any:
    """Perform an authenticated GET request."""
    auth = get_auth()
    query = {**(params or {}), **auth}
    logger.debug(">>> GET %s", path)
    if params:
        logger.debug("    %s", params)
    response = httpx.get(f"{BASE_URL}{path}", params=query)
    logger.debug("<<< %s", response.status_code)
    logger.debug("    %s", response.text)
    _check(response, f"GET {path}")
    return response.json()


def post(path: str, data: dict | None = None) -> dict:
    """Perform an authenticated POST request."""
    auth = get_auth()
    query = {**(data or {}), **auth}
    logger.debug(">>> POST %s", path)
    if data:
        logger.debug("    %s", data)
    response = httpx.post(f"{BASE_URL}{path}", params=query)
    logger.debug("<<< %s", response.status_code)
    logger.debug("    %s", response.text)
    _check(response, f"POST {path}")
    return response.json()


def _check(response: httpx.Response, context: str) -> None:
    if not response.is_success:
        print(
            f"Error: {context} failed with status {response.status_code}: {response.text}",
            file=sys.stderr,
        )
        raise SystemExit(1)
