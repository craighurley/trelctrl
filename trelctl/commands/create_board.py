import typer

from trelctl.trello import boards

app = typer.Typer()


@app.command()
def create_board(name: str = typer.Argument(..., help="Name of the new board")) -> None:
    """Create a new Trello board."""
    board = boards.create_board(name)
    print(f'Created board: "{board["name"]}" (id: {board["id"]})')
