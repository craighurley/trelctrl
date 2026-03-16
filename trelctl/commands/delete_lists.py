import typer

from trelctl.trello import boards, lists

app = typer.Typer()


@app.command()
def delete_lists(
    board: str = typer.Option(..., "--board", help="Board name or ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Delete (archive) all lists from a Trello board."""
    resolved_board = boards.resolve_board(board)
    board_id = resolved_board["id"]
    board_lists = lists.get_lists(board_id)

    if not board_lists:
        print("No lists found on board.")
        return

    if not yes:
        typer.confirm(f"Archive {len(board_lists)} list(s) from board?", abort=True)

    count = 0
    for lst in board_lists:
        lists.archive_list(lst["id"])
        print(f'Archived list: "{lst["name"]}" (id: {lst["id"]})')
        count += 1

    print(f"Done. Archived {count} list(s).")
