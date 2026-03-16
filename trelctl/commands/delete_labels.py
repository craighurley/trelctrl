import typer

from trelctl.trello import boards, labels

app = typer.Typer()


@app.command()
def delete_labels(
    board: str = typer.Option(..., "--board", help="Board name or ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Delete all labels from a Trello board."""
    resolved_board = boards.resolve_board(board)
    board_id = resolved_board["id"]
    board_labels = labels.get_labels(board_id)

    if not board_labels:
        print("No labels found on board.")
        return

    if not yes:
        typer.confirm(f"Delete {len(board_labels)} label(s) from board?", abort=True)

    count = 0
    for lbl in board_labels:
        labels.delete_label(lbl["id"])
        print(f'Deleted label: "{lbl["name"]}" (id: {lbl["id"]})')
        count += 1

    print(f"Done. Deleted {count} label(s).")
