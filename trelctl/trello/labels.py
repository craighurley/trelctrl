import sys

from . import client


def get_labels(board_id: str) -> list[dict]:
    """Fetch all labels for a board."""
    return client.get(f"/boards/{board_id}/labels")


def resolve_label_ids(board_id: str, label_names: list[str]) -> list[str]:
    """Resolve label names to their IDs (case-insensitive).

    Warns to stderr and skips any label name not found on the board.
    Returns a list of resolved label IDs.
    """
    if not label_names:
        return []

    labels = get_labels(board_id)
    label_map: dict[str, str] = {lbl["name"].lower(): lbl["id"] for lbl in labels}

    resolved: list[str] = []
    for name in label_names:
        label_id = label_map.get(name.lower())
        if label_id:
            resolved.append(label_id)
        else:
            print(f"Warning: label '{name}' not found on board — skipping.", file=sys.stderr)

    return resolved
