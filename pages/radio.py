import os
import logging
from textual import work
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, LoadingIndicator, DataTable, Input
from textual.message import Message
from textual.events import Click
from templates import BaseTemplate
import pyfiglet 
from utils.shoutcast_radio import ShoutcastRadio, ShoutcastRadioPlayer

logging.basicConfig(
    filename='example.log',
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)
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
        row_index = event.y
        if 0 <= row_index < len(self.stations):
            self.post_message(self.Selected(self.stations[row_index]))

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

class RadioPage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Radio Page")
        self.stations = []
        self.radio = ShoutcastRadio()
        self.radio_player = ShoutcastRadioPlayer()

    def compose_main_content(self) -> ComposeResult:
        with Container(id="main-right", classes="main-right"):
            banner = pyfiglet.figlet_format(os.getenv('APP_NAME', ''), font="slant", width=100)
            yield Static(banner, id="main-right-title", classes="main-right-title")
            yield Container(SearchInput(id="search-input"))
            yield Container(
                LoadingIndicator(id="main-right-body-loading"),
                id="main-right-body",
                classes="main-right-body"
            )

    async def _update_stations_display(self, stations: list) -> None:
        body = self.query_one("#main-right-body")
        await self.query_one("#main-right-body-loading").remove()
        
        try:
            await self.query_one("#main-right-body-content").remove()
        except:
            pass

        if not stations:
            content = Static("No stations found", id="main-right-body-content")
        else:
            content = RadioDataTable(id="main-right-body-content")
            content.add_rows(stations)
        
        await body.mount(content)

    @work(exclusive=True)
    async def on_mount(self) -> None:
        self.stations = await self.radio.get_now_playing_stations(limit=10, async_request=True)
        await self._update_stations_display(self.stations)

    @work(exclusive=True)
    async def on_search_input_submitted(self, event: SearchInput.Submitted) -> None:
        loading = LoadingIndicator(id="main-right-body-loading")
        await self.query_one("#main-right-body").mount(loading)
        
        self.stations = await self.radio.get_now_playing_stations(
            ct=event.value,
            limit=10,
            async_request=True
        )
        await self._update_stations_display(self.stations)

    def on_click(self, event: Click) -> None:
        search_input = self.query_one("#search-input")
        if (
            event.widget != search_input and 
            self.screen.focused and 
            isinstance(self.screen.focused, SearchInput)
        ):
            self.screen.focused.blur()

    def on_radio_data_table_selected(self, message) -> None:
        """Handle station selection from the radio page."""
        stream_url = message.station['stream_url']
        self.radio_player.play_stream_url(stream_url)