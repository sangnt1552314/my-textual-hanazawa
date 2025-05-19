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
from templates import BaseTemplate
from utils.shoutcast_radio import *
from utils.audio_player import ShoutcastRadioPlayer

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
        self.caches = {
            "genres": False,
            "top_stations": False,
        }

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True,
            id="radio-header"
        )

        yield Input(placeholder="Search...(supports querying multiple artists in the same query by using '||'. ex: ct=madonna||u2||beyonce up to 10 artists)", id="search_input")

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

        yield Footer()

    @work(exclusive=True)
    async def on_mount(self) -> None:
        await self._init_genre_list()

    @work(exclusive=True)
    async def on_tabbed_content_tab_activated(self, message: TabbedContent.TabActivated) -> None:
        tab_id = message.tab.id
        match tab_id:
            case "tab_genres":
                await self._init_genre_list()
            case "tab_stations":
                await self._init_top_stations()
        
    @work(exclusive=True)
    async def on_list_view_selected(self, message: ListView.Selected) -> None:
        list_view = message.list_view
        match list_view.id:
            case "top_stations_list" | "playing_station_list":
                try:
                    station = message.item.children[0]
                    station_id = re.search(r"station-(\d+)", station.id).group(1)
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
            case "genre_list":
                try:
                    genre = message.item.children[0]
                    genre_id = re.search(r"genre-(\d+)", genre.id).group(1)
                    stations_list_view = self.query_one("#playing_station_list", ListView)
                    stations_list_view.clear()
                    stations = await self.shoutcast_radio.get_stations_by_genre_or_bitrate(genre_id=genre_id, async_request=True)
                    if stations:
                        for station in stations:
                            stations_list_view.append(
                                ListItem(Label(station["name"], id=f"station-{station["id"]}")))
                    else:
                        stations_list_view.append(ListItem(Label("No stations found.")))
                except Exception as e:
                    logger.error(f"Error loading stations by genre: {e}")
                    self.notify(f"Error loading stations by genre: {str(e)}", severity="error")

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
                        ListItem(Label(station["name"], id=f"station-{station["id"]}")))
            else:
                stations_list_view.append(ListItem(Label("No stations found.")))

    async def _init_genre_list(self, force_reload = False):
        if force_reload:
            self.caches["genres"] = False

        if self.caches["genres"]:
            return

        genre_list_view = self.query_one("#genre_list", ListView)

        try:
            genres = await self.shoutcast_radio.get_primary_genres(async_request=True)
        except Exception as e:
            self.notify(f"Error loading genres", severity="error")
            return

        if genres:
            genre_list_view.clear()
            for genre in genres:
                genre_list_view.append(ListItem(Label(genre["name"], id=f"genre-{genre["id"]}")))
        else:
            genre_list_view.append(ListItem(Label("No genres available.")))

        if not self.caches["genres"] and not force_reload:
            self.caches["genres"] = True

    async def _init_top_stations(self, force_reload = False):
        if force_reload:
            self.caches["top_stations"] = False

        if self.caches["top_stations"]:
            return

        stations_list_view = self.query_one("#top_stations_list", ListView)
        
        if stations_list_view.children:
            return
        try:
            stations = await self.shoutcast_radio.get_top_500_stations(async_request=True, limit=(20, 0))
        except Exception as e:
            self.notify(f"Error loading top stations", severity="error")
            return
        
        if stations:
            stations_list_view.clear()
            for station in stations:
                stations_list_view.append(ListItem(Label(station["name"], id=f"station-{station["id"]}")))
        else:
            stations_list_view.append(ListItem(Label("No stations available.")))

        if not self.caches["top_stations"] and not force_reload:
            self.caches["top_stations"] = True