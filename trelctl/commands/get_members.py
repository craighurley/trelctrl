import csv
import sys

import typer

from trelctl.trello import boards, client

app = typer.Typer()


@app.command()
def get_members(
    board: str = typer.Option(..., "--board", help="Board name or ID"),
) -> None:
    """Get all members of a board in CSV format."""
    resolved_board = boards.resolve_board(board)
    members: list = client.get(f"/boards/{resolved_board['id']}/members")

    writer = csv.DictWriter(sys.stdout, fieldnames=["name"], lineterminator="\n")
    writer.writeheader()
    for member in members:
        writer.writerow({"name": member["id"]})
