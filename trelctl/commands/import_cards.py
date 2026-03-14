from pathlib import Path

import typer

from trelctl import parser
from trelctl.trello import boards, cards, labels, lists

app = typer.Typer()


@app.command()
def import_cards(
    file: Path = typer.Argument(..., help="CSV file with cards to import"),
    board: str = typer.Option(..., "--board", help="Board name or ID"),
    list_name: str = typer.Option(..., "--list", help="List name or ID"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without creating resources"),
) -> None:
    """Import cards from a CSV file into a Trello list."""
    card_rows = parser.parse_cards(file)
    resolved_board = boards.resolve_board(board)
    board_id = resolved_board["id"]
    resolved_list = lists.resolve_list(board_id, list_name)
    list_id = resolved_list["id"]

    # Pre-fetch all label IDs needed (resolve unique names up front)
    all_label_names: list[str] = []
    for row in card_rows:
        for lbl in row.labels:
            if lbl not in all_label_names:
                all_label_names.append(lbl)

    label_id_map: dict[str, str] = {}
    if all_label_names:
        board_labels = labels.get_labels(board_id)
        label_lookup = {lbl["name"].lower(): lbl["id"] for lbl in board_labels}
        for name in all_label_names:
            lid = label_lookup.get(name.lower())
            if lid:
                label_id_map[name] = lid
            else:
                import sys

                print(f"Warning: label '{name}' not found on board — skipping.", file=sys.stderr)

    count = 0
    for row in card_rows:
        resolved_label_ids = [label_id_map[lbl] for lbl in row.labels if lbl in label_id_map]
        due = parser.due_date_to_rfc3339(row.due_date) if row.due_date else ""

        if dry_run:
            print(f'[dry-run] Would create card: "{row.name}"')
            count += 1
            continue

        card = cards.create_card(
            list_id=list_id,
            name=row.name,
            desc=row.description,
            label_ids=resolved_label_ids,
            due=due,
            member_ids=row.members,
        )
        card_id = card["id"]

        if row.checklist:
            checklist = cards.create_checklist(card_id)
            checklist_id = checklist["id"]
            for item in row.checklist:
                cards.create_check_item(checklist_id, item)

        print(f'Created card: "{card["name"]}" (id: {card_id})')
        count += 1

    if not dry_run:
        print(f"Done. Created {count} card(s).")
    else:
        print(f"Done. Would create {count} card(s).")
