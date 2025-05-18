import os
import logging
import time
import pyfiglet
from textual import work
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Vertical,
    Horizontal,
    VerticalGroup,
    VerticalScroll
)
from textual.widgets import (
    Static,
    LoadingIndicator,
    DataTable,
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
from textual.message import Message
from textual.events import Click
from templates import BaseTemplate
from utils.shoutcast_radio import *

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=f"""../logs/dev.log""",
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
                #     yield ListView(
                #         ListItem(Label("Loading stations...")),
                #         id="now_playing_stations_list"
                #     )

                with TabbedContent(id="section_tabs"):
                    with TabPane("Genres", id="tab_genres"):
                        yield ListView(
                            ListItem(Label("Loading genres...")),
                            id="genre_list"
                        )
                    with TabPane("Stations", id="tab_stations"):
                        yield ListView(
                            ListItem(Label("Loading stations...")),
                            id="stations_list"
                        )

            with Container(id="main_content"):
                welcome_text = pyfiglet.figlet_format(os.getenv('APP_NAME', 'Radio'), font="slant")
                yield Label(welcome_text, classes="header")
                yield ListView(
                    ListItem(Label("Song 1 – Artist A")),
                    ListItem(Label("Song 2 – Artist B")),
                    ListItem(Label("Song 3 – Artist C")),
                    id="playlist_tracks"
                )

        yield Footer(id="radio-footer")

    @work(exclusive=True)
    async def on_mount(self) -> None:
        genre_list_view = self.query_one("#genre_list", ListView)
        genre_list_view.clear()
        genres = await self.shoutcast_radio.get_all_genres(async_request=True)
        if genres:
            for genre in genres:
                genre_list_view.append(ListItem(Label(genre["name"])))
        else:
            genre_list_view.append(ListItem(Label("No genres available.")))

        stations_list_view = self.query_one("#stations_list", ListView)
        stations_list_view.clear()
        stations = await self.shoutcast_radio.get_now_playing_stations(async_request=True)
        if stations:
            for station in stations:
                stations_list_view.append(ListItem(Label(station["name"])))
        else:
            stations_list_view.append(ListItem(Label("No stations available.")))
