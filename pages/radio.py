import os
import logging
import time
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
import pyfiglet

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=f"""../logs/dev-{time.strftime("%Y-%m-%d")}.log""",
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

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True,
            id="radio-header"
        )

        yield Input(placeholder="Search...", id="search_input")

        with Container(id="body_container"):
            with Container(id="sidebar"):
                with TabbedContent(id="section_tabs"):
                    with TabPane("Genres", id="tab_genres"):
                        yield ListView(
                            ListItem(Label("Made For You")),
                            ListItem(Label("Recently Played")),
                            ListItem(Label("Liked Songs")),
                            ListItem(Label("Albums")),
                            ListItem(Label("Artists")),
                            ListItem(Label("Podcasts")),
                            id="genre_list"
                        )
                    with TabPane("Stations", id="tab_stations"):
                        yield ListView(
                            ListItem(Label("Jazz Classics")),
                            ListItem(Label("Rock Hits")),
                            ListItem(Label("Synthwave / Retro Electro")),
                            ListItem(Label("City Pop Essentials")),
                            ListItem(Label("Study Beats")),
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

    @work(exclusive=True, thread=True)
    async def on_mount(self) -> None:
        pass

    def on_click(self, event: Click) -> None:
        pass
        # logger.debug(f"Clicked on {event.sender.id}")