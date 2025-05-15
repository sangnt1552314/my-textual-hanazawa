import os
from textual import work
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    Static,
    LoadingIndicator,
    DataTable,
)
from textual.message import Message
from textual.events import Click
from templates import BaseTemplate
import pyfiglet 
from utils.shoutcast_radio import ShoutcastRadio

class RadioDataTable(DataTable):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.add_column("Name")
        self.add_column("Genre")
        self.stations = []

    class Selected(Message):
        def __init__(self, station: dict) -> None:
            self.station = station
            super().__init__()

    def add_rows(self, rows: list) -> None:
        self.stations = rows
        for row in rows:
            self.add_row(row["name"], row["genre"])

    def on_click(self, event: Click) -> None:
        # Get the selected row index
        row_index = event.y
        if 0 <= row_index < len(self.stations):
            # Get the station data for the selected row
            selected_station = self.stations[row_index]
            # Post the message with the selected station
            self.post_message(self.Selected(selected_station))

class HomePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Home Page")
        self.stations = []

    def compose_main_content(self) -> ComposeResult:
        with Container(id="main-right", classes="main-right"):
            # Create a banner using pyfiglet
            banner = pyfiglet.figlet_format(os.getenv('APP_NAME', ''), font="slant", width=100)
            yield Static(banner, id="main-right-title", classes="main-right-title")

            # create table of music stations
            with Container(id="main-right-body", classes="main-right-body"):
                yield LoadingIndicator(id="main-right-body-loading", classes="main-right-body-loading")

    @work(exclusive=True)  
    async def on_mount(self) -> None:
        await self.update_main_content()

    async def update_main_content(self) -> None:
        radio = ShoutcastRadio()
        self.stations = await radio.get_now_playing_stations(ct="pop", limit=10, async_request=True)

        if self.stations:
            # Remove the loading indicator
            await self.query_one("#main-right-body-loading").remove()

            table = RadioDataTable(id="main-right-body-content", classes="main-right-body-content")
            table.add_rows(self.stations)

            # Mount the new content to the container
            await self.query_one("#main-right-body").mount(table)
