import os
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, DataTable
from templates import BaseTemplate
import pyfiglet
from utils.shoutcast_radio import ShoutcastRadio

from rich.text import Text

class HomePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Home Page")

    def compose_main_content(self) -> ComposeResult:
        with Container(id="main-right", classes="main-right"):
            # Create a banner using pyfiglet
            banner = pyfiglet.figlet_format(os.getenv('APP_NAME', ''), font="slant")
            yield Static(banner, id="main-right-title", classes="main-right-title")

            # create table of music stations
            with Container(id="main-right-table", classes="main-right-table"):
                yield Static("Now Playing Stations", id="main-right-table-title", classes="main-right-table-title")
                yield DataTable()

    def on_mount(self) -> None:
        # Get the list of now playing stations
        shoutcast_radio = ShoutcastRadio()
        stations = shoutcast_radio.get_now_playing_stations(ct="us", limit=10)
        table = self.query_one(DataTable)
        table.add_columns(*stations[0])
        for row in stations[1:]:
            # Adding styled and justified `Text` objects instead of plain strings.
            styled_row = [
                Text(str(cell), style="italic #03AC13", justify="right") for cell in row
            ]
            table.add_row(*styled_row)