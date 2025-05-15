import os
import logging
from textual.logging import TextualHandler
from textual import work
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    Static,
    LoadingIndicator,
    DataTable,
    Input
)
from textual.message import Message
from textual.events import Click
from templates import BaseTemplate
import pyfiglet 
from utils.shoutcast_radio import ShoutcastRadio

# Configure logging to use TextualHandler
logging.basicConfig(filename='example.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='a') # 'a' for append, 'w' to overwrite
logger = logging.getLogger(__name__)

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

class SearchInput(Input):
    CSS = """
    Container {
        align: center middle;
    }

    Input {
        width: 60;
    }
    """

    class Submitted(Message):
        """Search submitted message."""
        def __init__(self, sender: "SearchInput", value: str, validation_result: bool | None) -> None:
            self.value = value
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.placeholder = "Searching for ..."

    def on_input_submitted(self, event: Input.Submitted) -> None:
        search_term = event.value
        if search_term:
            self.post_message(self.Submitted(self, search_term, None))

class HomePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Home Page")
        self.stations = []

    def compose_main_content(self) -> ComposeResult:
        with Container(id="main-right", classes="main-right"):
            # Create a banner using pyfiglet
            banner = pyfiglet.figlet_format(os.getenv('APP_NAME', ''), font="slant", width=100)
            yield Static(banner, id="main-right-title", classes="main-right-title")

            yield Container(SearchInput(id="search-input"))

            # create table of music stations
            with Container(id="main-right-body", classes="main-right-body"):
                yield LoadingIndicator(id="main-right-body-loading", classes="main-right-body-loading")

    @work(exclusive=True)  
    async def on_mount(self) -> None:
        await self.update_main_content()

    @work(exclusive=True)
    async def on_search_input_submitted(self, event: SearchInput.Submitted) -> None:
        search_term = event.value

        # Show loading indicator
        loading = LoadingIndicator(id="main-right-body-loading", classes="main-right-body-loading")
        await self.query_one("#main-right-body").mount(loading)

        # Remove existing content if any
        try:
            await self.query_one("#main-right-body-content").remove()
        except:
            pass

        # Fetch stations with search term
        radio = ShoutcastRadio()
        self.stations = await radio.get_now_playing_stations(ct=search_term, limit=10, async_request=True)

        # Remove the loading indicator
        await loading.remove()

        if not self.stations:
            message = Static("No stations found", id="main-right-body-content", classes="main-right-body-content")
            await self.query_one("#main-right-body").mount(message)
        else:
            table = RadioDataTable(id="main-right-body-content", classes="main-right-body-content")
            table.add_rows(self.stations)
            await self.query_one("#main-right-body").mount(table)

    def on_click(self, event: Click) -> None:
        search_input = self.query_one("#search-input")
        if event.widget != search_input:
            if self.screen.focused and isinstance(self.screen.focused, SearchInput):
                self.screen.focused.blur()

    async def update_main_content(self, ct="") -> None:
        radio = ShoutcastRadio()
        self.stations = await radio.get_now_playing_stations(ct=ct, limit=10, async_request=True)

        if not self.stations:
            # Remove the loading indicator
            await self.query_one("#main-right-body-loading").remove()

            message = Static("No stations found", id="main-right-body-content", classes="main-right-body-content")
            await self.query_one("#main-right-body").mount(message)

        if self.stations:
            # Remove the loading indicator
            await self.query_one("#main-right-body-loading").remove()

            table = RadioDataTable(id="main-right-body-content", classes="main-right-body-content")
            table.add_rows(self.stations)

            # Mount the new content to the container
            await self.query_one("#main-right-body").mount(table)
