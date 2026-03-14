import sys

from . import client


def resolve_board(name_or_id: str) -> dict:
    """Resolve a board by name (case-insensitive) or ID.

    Fetches all boards for the authenticated user and returns the matching one.
    Exits with an error if no match is found.
    """
    boards: list = client.get("/members/me/boards")

    # Try name match first (case-insensitive)
    lower = name_or_id.lower()
    for board in boards:
        if board["name"].lower() == lower:
            return board

    # Fall back to ID match
    for board in boards:
        if board["id"] == name_or_id:
            return board

    print(
        f"Error: board '{name_or_id}' not found. Provide a valid board name or ID.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def create_board(name: str) -> dict:
    """Create a new Trello board with the given name."""
    return client.post("/boards", {"name": name})
