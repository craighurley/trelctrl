from . import client


def create_card(
    list_id: str,
    name: str,
    desc: str = "",
    label_ids: list[str] | None = None,
    due: str = "",
    member_ids: list[str] | None = None,
) -> dict:
    """Create a card in the given list."""
    data: dict[str, str] = {"name": name, "idList": list_id}
    if desc:
        data["desc"] = desc
    if label_ids:
        data["idLabels"] = ",".join(label_ids)
    if due:
        data["due"] = due
    if member_ids:
        data["idMembers"] = ",".join(member_ids)
    return client.post("/cards", data)


def create_checklist(card_id: str) -> dict:
    """Create a checklist named 'Checklist' on a card."""
    return client.post(f"/cards/{card_id}/checklists", {"name": "Checklist"})


def create_check_item(checklist_id: str, name: str) -> dict:
    """Add a check item to a checklist."""
    return client.post(f"/checklists/{checklist_id}/checkItems", {"name": name})


def get_board_cards(board_id: str) -> list[dict]:
    """Fetch all cards on a board."""
    return client.get(f"/boards/{board_id}/cards")


def get_list_cards(list_id: str) -> list[dict]:
    """Fetch all cards in a list."""
    return client.get(f"/lists/{list_id}/cards")


def get_card_checklists(card_id: str) -> list[dict]:
    """Fetch all checklists for a card."""
    return client.get(f"/cards/{card_id}/checklists")


def delete_card(card_id: str) -> None:
    """Delete a card by ID."""
    client.delete(f"/cards/{card_id}")
