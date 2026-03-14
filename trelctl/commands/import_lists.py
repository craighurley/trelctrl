from pathlib import Path

import typer

from trelctl import parser
from trelctl.trello import boards, lists

app = typer.Typer()


@app.command()
def import_lists(
    file: Path = typer.Argument(..., help="CSV file with lists to import"),
    board: str = typer.Option(..., "--board", help="Board name or ID"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without creating resources"),
) -> None:
    """Import lists from a CSV file into a Trello board."""
    names = parser.parse_lists(file)
    resolved_board = boards.resolve_board(board)
    board_id = resolved_board["id"]

    count = 0
    for name in names:
        if dry_run:
            print(f'[dry-run] Would create list: "{name}"')
        else:
            lst = lists.create_list(board_id, name)
            print(f'Created list: "{lst["name"]}" (id: {lst["id"]})')
        count += 1

    if not dry_run:
        print(f"Done. Created {count} list(s).")
    else:
        print(f"Done. Would create {count} list(s).")
