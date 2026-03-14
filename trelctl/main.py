import typer
from dotenv import load_dotenv

from trelctl.commands.create_board import create_board
from trelctl.commands.get_cards import get_cards
from trelctl.commands.get_lists import get_lists
from trelctl.commands.get_members import get_members
from trelctl.commands.import_cards import import_cards
from trelctl.commands.import_lists import import_lists

load_dotenv()

app = typer.Typer(no_args_is_help=True)

board_app = typer.Typer(no_args_is_help=True)
import_app = typer.Typer(no_args_is_help=True)
get_app = typer.Typer(no_args_is_help=True)

app.add_typer(board_app, name="create")
app.add_typer(import_app, name="import")
app.add_typer(get_app, name="get")

board_app.command("board")(create_board)
import_app.command("lists")(import_lists)
import_app.command("cards")(import_cards)
get_app.command("lists")(get_lists)
get_app.command("cards")(get_cards)
get_app.command("members")(get_members)
