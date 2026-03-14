import csv
import sys

import typer

from trelctl.trello import boards, lists

app = typer.Typer()


@app.command()
def get_lists(
    board: str = typer.Option(..., "--board", help="Board name or ID"),
) -> None:
    """Get all lists from a board in CSV format."""
    resolved_board = boards.resolve_board(board)
    board_lists = lists.get_lists(resolved_board["id"])

    writer = csv.DictWriter(sys.stdout, fieldnames=["name"])
    writer.writeheader()
    for lst in board_lists:
        writer.writerow({"name": lst["name"]})
