import typer

from trelctl.trello import boards, cards

app = typer.Typer()


@app.command()
def delete_cards(
    board: str = typer.Option(..., "--board", help="Board name or ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Delete all cards from a Trello board."""
    resolved_board = boards.resolve_board(board)
    board_id = resolved_board["id"]
    board_cards = cards.get_board_cards(board_id)

    if not board_cards:
        print("No cards found on board.")
        return

    if not yes:
        typer.confirm(f"Delete {len(board_cards)} card(s) from board?", abort=True)

    count = 0
    for card in board_cards:
        cards.delete_card(card["id"])
        print(f'Deleted card: "{card["name"]}" (id: {card["id"]})')
        count += 1

    print(f"Done. Deleted {count} card(s).")
