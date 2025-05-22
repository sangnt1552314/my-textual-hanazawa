import re
import os
import logging
import pyfiglet
from textual import work
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Vertical,
    Horizontal
)
from textual.widgets import (
    Input,
    Header,
    Footer,
    ListView,
    ListItem,
    Label,
    TabbedContent,
    TabPane,
    Button
)
from templates import BaseTemplate
from utils.shoutcast_radio import *
from utils.audio_player import ShoutcastRadioPlayer

logging.basicConfig(
    filename=f"dev.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w'  # a = append, w = overwrite
)
logger = logging.getLogger(__name__)


# Radio Page
class RadioPage(BaseTemplate):
    CSS_PATH = "../assets/css/radio_page/main.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "switch_mode('youtube')", "Youtube"),
    ]

    def __init__(self) -> None:
        super().__init__(subtitle="Radio Page")
        self.shoutcast_radio = ShoutcastRadio()
        self.radio_player = ShoutcastRadioPlayer()
        self.current_stream_url = None

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True,
            id="radio-header"
        )

        yield Input(placeholder="Search...", 
                    id="search_input", 
                    tooltip="supports querying multiple artists in the same query by using '||'. ex: ct=madonna||u2||beyonce up to 10 artists")

        with Container(id="body_container"):
            with Vertical(id="sidebar"):
                with TabbedContent(id="section_tabs"):
                    with TabPane("Genres", id="tab_genres"):
                        yield ListView(
                            id="genre_list",
                            classes="tab-item-list"
                        )
                    with TabPane("Top Stations", id="tab_stations"):
                        yield ListView(
                            id="top_stations_list",
                            classes="tab-item-list"
                        )

            with Container(id="main_content"):
                welcome_text = pyfiglet.figlet_format(
                    os.getenv('APP_NAME', 'Radio'), font="slant")
                yield Label(welcome_text, classes="header")
                with ListView(
                    id="playing_station_list"
                ):
                    yield ListItem(Label("No stations found."))

        with Container(id="player_bar"):
            with Horizontal():
                yield Button("⏵", id="play_pause_button", variant="primary", disabled=True)
                yield Label("Now Playing: ", id="player_status")
                yield Label("No station selected", id="current_station")
        
        yield Footer()

    @work(exclusive=True)
    async def on_mount(self) -> None:
        await self._init_genre_list()

    @work(exclusive=True)
    async def on_tabbed_content_tab_activated(self, message: TabbedContent.TabActivated) -> None:
        tab_id = message.tab.id.replace("--content-tab-", "")
        match tab_id:
            case "tab_genres":
                await self._init_genre_list()
            case "tab_stations":
                await self._init_top_stations()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "play_pause_button":
            if self.radio_player.is_playing:
                self.radio_player.stop()
                event.button.label = "⏵" 
            else:
                self.radio_player.play_stream_url(self.current_stream_url)
                event.button.label = "⏸"

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        list_view = message.list_view
        match list_view.id:
            case "top_stations_list" | "playing_station_list":
                try:
                    station = message.item.children[0]
                    station_id = re.search(r"station-(\d+)", station.id).group(1)
                    stream_url = self.shoutcast_radio.get_station_stream_url(station_id)
                    self.current_stream_url = stream_url

                    if not self.radio_player.is_available:
                        self.notify("Player is not available. Please install player.", severity="error")
                        return

                    if not stream_url:
                        self.notify("Could not get stream URL for this station", severity="error")
                        return

                    self.notify(f"Playing station {station_id}")

                    current_station_label = self.query_one("#current_station", Label)
                    current_station_label.update(station._content)

                    self.query_one("#play_pause_button", Button).disabled = False
                    self.query_one("#play_pause_button", Button).label = "⏸"

                    self.radio_player.play_stream_url(stream_url)
                except Exception as e:
                    logger.error(f"Error playing station: {e}")
                    self.notify(f"Error playing station: {str(e)}", severity="error")
            case "genre_list":
                try:
                    genre = message.item.children[0]
                    genre_id = re.search(r"genre-(\d+)", genre.id).group(1)

                    stations_list_view = self.query_one("#playing_station_list", ListView)
                    stations_list_view.clear()

                    stations = self.shoutcast_radio.get_stations_by_genre_or_bitrate_sync(genre_id=genre_id)

                    if not stations:
                        stations_list_view.append(ListItem(Label("No stations found.")))
                        return

                    for station in stations:
                        station_name = self._sanitize_station_name(station["name"])
                        station_id = f"station-{station["id"]}"
                        stations_list_view.append(ListItem(Label(station_name, id=station_id, classes="station-item")))
                except Exception as e:
                    logger.error(f"Error loading stations by genre: {e}")
                    self.notify(f"Error loading stations by genre: {str(e)}", severity="error")

    @work(exclusive=True)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        search_query = event.value.strip()
        search_query = search_query.replace(" ", "+")

        stations_list_view = self.query_one("#playing_station_list", ListView)
        stations_list_view.clear()

        if search_query == "":
            stations_list_view.append(ListItem(Label("No stations found.")))
            return

        if search_query:
            try:
                stations = await self.shoutcast_radio.get_now_playing_stations(ct=search_query)
                if not stations:
                    stations_list_view.append(ListItem(Label("No stations found.")))
                    return

                for station in stations:
                    station_name = self._sanitize_station_name(station["name"])
                    station_id = f"station-{station["id"]}"
                    stations_list_view.append(ListItem(Label(station_name, id=station_id, classes="station-item")))
            except Exception as e:
                stations_list_view.append(ListItem(Label("No stations found.")))
                self.notify(f"Error loading station", severity="error")
                return

    async def _init_genre_list(self):
        genre_list_view = self.query_one("#genre_list", ListView)

        if genre_list_view.children:
            return

        try:
            genres = await self.shoutcast_radio.get_primary_genres()
            if genres:
                genre_list_view.clear()
                for genre in genres:
                    genre_list_view.append(ListItem(Label(genre["name"], id=f"genre-{genre["id"]}")))
            else:
                genre_list_view.append(ListItem(Label("No genres available.")))
        except Exception as e:
            self.notify(f"Error loading genres", severity="error")
            return

    async def _init_top_stations(self):
        stations_list_view = self.query_one("#top_stations_list", ListView)

        if stations_list_view.children:
            return

        try:
            stations = await self.shoutcast_radio.get_top_500_stations(limit=(20, 0))
            if stations:
                stations_list_view.clear()
                for station in stations:
                    stations_list_view.append(ListItem(Label(station["name"], id=f"station-{station["id"]}")))
            else:
                stations_list_view.append(ListItem(Label("No stations available.")))
        except Exception as e:
            self.notify(f"Error loading top stations", severity="error")
            return

    def _sanitize_station_name(self, name: str) -> str:
        """Sanitize station name by removing problematic characters."""
        # Remove or replace problematic characters
        name = re.sub(r'[\[\]]', '', name)  # Remove square brackets
        # Remove non-printable characters
        name = re.sub(r'[^\x20-\x7E]', '', name)
        name = name.strip()
        return name if name else "Unnamed Station"
