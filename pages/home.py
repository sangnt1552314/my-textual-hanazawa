import os
from textual import work
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    Static,
    LoadingIndicator,
    DataTable,
)
from templates import BaseTemplate
import pyfiglet 
from utils.shoutcast_radio import ShoutcastRadio

class HomePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Home Page")

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
        stations = await radio.get_now_playing_stations(ct="pop", limit=10, async_request=True)

        if stations:
            # Remove the loading indicator
            await self.query_one("#main-right-body-loading").remove()

            # Create a DataTable to display the stations
            table = DataTable(id="main-right-body-content", classes="main-right-body-content")
            table.add_column("Name")
            table.add_column("Genre")
            table.add_rows([
                [station["name"], station["genre"]]
                for station in stations
            ])
            
            # Mount the new content to the container
            await self.query_one("#main-right-body").mount(table)