import re
import os
import logging
import pyfiglet
from textual import work
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Vertical,
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
    )
from textual.message import Message
from textual.events import Click
from templates import BaseTemplate
from utils.shoutcast_radio import *

logging.basicConfig(
    filename=f"dev.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Radio Page
class RadioPage(BaseTemplate):
    CSS_PATH = "../assets/css/radio_page/main.tcss"

    def __init__(self) -> None:
        super().__init__(subtitle="Radio Page")
        self.shoutcast_radio = ShoutcastRadio()
        self.radio_player = ShoutcastRadioPlayer()

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True,
            id="radio-header"
        )

        yield Input(placeholder="Search...", id="search_input")

        with Container(id="body_container"):
            with Vertical(id="sidebar"):
                # with Container(id="now-playing"):
                #     yield Label("Now Playing Station", id="now-title")

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
                welcome_text = pyfiglet.figlet_format(os.getenv('APP_NAME', 'Radio'), font="slant")
                yield Label(welcome_text, classes="header")
                yield ListView(
                    id="playing_station_list"
                )

        yield Footer(id="radio-footer")

    @work(exclusive=True)
    async def on_mount(self) -> None:
        await self._init_genre_list()

    @work(exclusive=True)
    async def on_click(self, event: Click) -> None:
        match event.widget.id:
            case "--content-tab-tab_stations":
                await self._init_top_stations()
            case station_id if station_id and re.match(r"nowplaying-station-\d+", station_id):
                try:
                    station_id = re.search(r"nowplaying-station-(\d+)", station_id).group(1)
                    stream_url = self.shoutcast_radio.get_station_stream_url(station_id)
                    
                    if not self.radio_player.is_available:
                        self.notify("VLC is not available. Please install VLC media player.", severity="error")
                        return
                        
                    if not stream_url:
                        self.notify("Could not get stream URL for this station", severity="error")
                        return
                    
                    self.radio_player.play_stream_url(stream_url)
                    self.notify(f"Playing station {station_id}")

                except RuntimeError as e:
                    self.notify(str(e), severity="error")
                except Exception as e:
                    logger.error(f"Error playing station: {e}")
                    self.notify(f"Error playing station: {str(e)}", severity="error")
            case _:
                pass

    @work(exclusive=True)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        search_query = event.value.strip()
        search_query = search_query.replace(" ", "+")

        if search_query == "":
            logger.debug("Search query is empty.")
            return
        
        if search_query:
            stations_list_view = self.query_one("#playing_station_list", ListView)
            stations_list_view.clear()
            stations = await self.shoutcast_radio.get_now_playing_stations(ct=search_query, async_request=True)
            if stations:
                for station in stations:
                    stations_list_view.append(
                        ListItem(
                            Label(
                                station["name"],
                                id=f"nowplaying-station-{station["id"]}"
                                )
                        ))
            else:
                stations_list_view.append(ListItem(Label("No stations found.")))

    async def _init_genre_list(self):
        genre_list_view = self.query_one("#genre_list", ListView)
        genres = await self.shoutcast_radio.get_all_genres(async_request=True)
        if genres:
            genre_list_view.clear()
            for genre in genres:
                genre_list_view.append(ListItem(Label(genre["name"])))
        else:
            genre_list_view.append(ListItem(Label("No genres available.")))

    async def _init_top_stations(self):
        stations_list_view = self.query_one("#top_stations_list", ListView)
        
        if stations_list_view.children:
            return
        
        stations = await self.shoutcast_radio.get_top_500_stations(async_request=True, limit=10)
        if stations:
            stations_list_view.clear()
            for station in stations:
                stations_list_view.append(ListItem(Label(station["name"])))
        else:
            stations_list_view.append(ListItem(Label("No stations available.")))