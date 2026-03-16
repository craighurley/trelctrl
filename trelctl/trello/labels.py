import random

from . import client

COLOURS = ["yellow", "purple", "blue", "red", "green", "orange", "black", "sky", "pink", "lime"]


def pick_colour(used: list[str]) -> str:
    """Pick a colour, preferring ones not already in use."""
    available = [c for c in COLOURS if c not in used]
    if available:
        return random.choice(available)
    return random.choice(COLOURS)


def get_labels(board_id: str) -> list[dict]:
    """Fetch all labels for a board."""
    return client.get(f"/boards/{board_id}/labels")


def create_label(board_id: str, name: str, used_colours: list[str] | None = None) -> dict:
    """Create a new label on a board with a random colour."""
    colour = pick_colour(used_colours or [])
    return client.post(f"/boards/{board_id}/labels", {"name": name, "color": colour})


def delete_label(label_id: str) -> None:
    """Delete a label by ID."""
    client.delete(f"/labels/{label_id}")
