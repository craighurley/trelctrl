import csv
import sys

import typer

from trelctl.trello import boards, cards, lists

app = typer.Typer()

_FIELDS = ["name", "description", "labels", "due_date", "checklist", "members"]


def _format_card(card: dict) -> dict[str, str]:
    """Map a Trello card API response to a CSV row dict."""
    # Labels: pipe-separated names
    label_names = "|".join(lbl.get("name", "") for lbl in card.get("labels", []))

    # Due date: extract YYYY-MM-DD from ISO timestamp
    due_raw = card.get("due") or ""
    due_date = due_raw[:10] if due_raw else ""

    # Members: pipe-separated IDs
    member_ids = "|".join(card.get("idMembers", []))

    # Checklists: fetch and flatten to pipe-separated items
    checklist_text = ""
    if card.get("badges", {}).get("checkItems", 0) > 0:
        checklists = cards.get_card_checklists(card["id"])
        items: list[str] = []
        for cl in checklists:
            for item in cl.get("checkItems", []):
                items.append(item["name"])
        checklist_text = "|".join(items)

    return {
        "name": card.get("name", ""),
        "description": card.get("desc", ""),
        "labels": label_names,
        "due_date": due_date,
        "checklist": checklist_text,
        "members": member_ids,
    }


@app.command()
def get_cards(
    board: str = typer.Option(..., "--board", help="Board name or ID"),
    list_name: str | None = typer.Option(None, "--list", help="Filter by list name or ID"),
) -> None:
    """Get all cards from a board (optionally filtered by list) in CSV format."""
    resolved_board = boards.resolve_board(board)
    board_id = resolved_board["id"]

    if list_name:
        resolved_list = lists.resolve_list(board_id, list_name)
        card_list = cards.get_list_cards(resolved_list["id"])
    else:
        card_list = cards.get_board_cards(board_id)

    writer = csv.DictWriter(sys.stdout, fieldnames=_FIELDS)
    writer.writeheader()
    for card in card_list:
        writer.writerow(_format_card(card))
