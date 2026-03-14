import sys

from . import client


def get_lists(board_id: str) -> list[dict]:
    """Fetch all lists for a board."""
    return client.get(f"/boards/{board_id}/lists")


def resolve_list(board_id: str, name_or_id: str) -> dict:
    """Resolve a list by name (case-insensitive) or ID within a board.

    Exits with an error if no match is found.
    """
    lists = get_lists(board_id)
    lower = name_or_id.lower()

    for lst in lists:
        if lst["name"].lower() == lower:
            return lst

    for lst in lists:
        if lst["id"] == name_or_id:
            return lst

    print(
        f"Error: list '{name_or_id}' not found on board. Provide a valid list name or ID.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def create_list(board_id: str, name: str) -> dict:
    """Create a new list on a board."""
    return client.post(f"/boards/{board_id}/lists", {"name": name})
