import os
import logging
from textual import work
from templates import BaseTemplate
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
    VerticalScroll,
    Grid,
)
from textual.widgets import (
    Input,
    Header,
    Footer,
    Label,
    Button,
    ListView,
    ListItem,
    Static,
    Rule
)
from textual.events import Click
from utils import youtube as yt
from utils.audio_player import *

logging.basicConfig(
    filename=f"dev.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w'  # a = append, w = overwrite
)
logger = logging.getLogger(__name__)

class YoutubeVideoContainer(Container):
    """Container for Youtube video items"""
    def __init__(self, video) -> None:
        super().__init__()
        self.video = video
        self.classes = "youtube_result_item_container"

    def compose(self) -> ComposeResult:
        with Container(classes="youtube_result_info"):
            # yield Static(self.video["ascii_art_thumbnail"], classes="youtube_result_thumbnail")
            yield Static(self.video["title"], classes="youtube_result_title")
            yield Static(f"{self.video["channel_title"]}", classes="youtube_result_metadata")

    # def on_click(self, event: Click) -> None:
    #     if self.video:
    #         logger.debug(f"Video clicked: {self.video['watch_url']}")
    #         audio_player = YoutubeAudioPlayer()
    #         audio_player.play_stream_url(self.video["watch_url"])

class YoutubePage(BaseTemplate):
    CSS_PATH = "../assets/css/youtube_page/main.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "switch_mode('radio')", "Radio"),
    ]

    def __init__(self) -> None:
        super().__init__(subtitle="Youtube")
        self.youtube_video_service = yt.YoutubeVideoService(use_google_api=True)
        self.playing_url = None

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True,
            id="youtube_header"
        )
        
        with Container(id="youtube_body_container"):
            with VerticalScroll(id="youtube_left_pane"):
                yield ListView(
                    ListItem(
                        Label("Trendings", id="youtube_left_pane_list_item_trendings", classes="youtube_left_pane_list_item_label"),
                        id="youtube_left_pane_list_item_trendings",
                        classes="youtube_left_pane_list_item"
                    ),
                    Rule(line_style="ascii"),
                    ListItem(
                        Label("Clear", id="youtube_left_pane_list_item_clear", classes="youtube_left_pane_list_item_label"),
                        id="youtube_left_pane_list_item_clear",
                        classes="youtube_left_pane_list_item"
                    ),
                    id="youtube_left_pane_list_view"
                )
                    
            with Horizontal(id="youtube_main_right"):
                with Vertical(id="youtube_search_container"):
                    yield Input(placeholder="Search...", 
                        id="youtube_search_input", 
                        tooltip="TBU")
                
                    with VerticalScroll(id="youtube_results_container"):
                        with Grid(id="youtube_results"):
                            yield Static(f"Hi, there is nothing right now!!!")
                    
        
        with Container(id="youtube_player_bar"):
            with Horizontal():
                yield Button("⏵", id="youtube_play_pause_button", variant="primary", disabled=True)
                yield Label("Now Playing: ", id="youtube_player_status")
                yield Label("No Video Selected", id="youtube_current_video")

        yield Footer()

    def on_mount(self) -> None:
        pass

    def on_input_submitted(self, event: Input.Submitted):
        logger.debug("Input submitted")
        """Handle search input submission"""
        search_input = self.query_one("#youtube_search_input", Input)
        search_query = search_input.value.strip()

        if search_query:
            videos = self.youtube_video_service.search_video(query=search_query, max_results=10, filters={"order": "viewCount"})

            if not videos:
                search_input.placeholder = "No results found"
                search_input.value = ""
                return
            
            # Clear existing results
            grid = self.query_one("#youtube_results", Grid)
            grid.remove_children()

            for video in videos:
                video_container = YoutubeVideoContainer(video=video)
                grid.mount(video_container)

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """Handle selection of list view items"""
        selected_item = message.item

        if selected_item.id == "youtube_left_pane_list_item_clear":
            self.clear_search_results()
    
    def on_click(self, event) -> None:
        if isinstance(event, Click):
            self.lose_search_input_focus(event)

    def clear_search_results(self) -> None:
        """Clear search results"""
        self.playing_url = None

        search_input = self.query_one("#youtube_search_input", Input)
        search_input.value = ""
        search_input.placeholder = "Search..."
        
        grid = self.query_one("#youtube_results", Grid)
        grid.remove_children()
        grid.mount(Static("Hi, there is nothing right now!!!"))

    def lose_search_input_focus(self, event: Click) -> None:
        search_input = self.query_one("#youtube_search_input", Input)
        
        if event.widget.id != "youtube_search_input":
            search_input.blur()
            self.set_focus(event.widget)

    def truncate_text(self, text: str, max_length: int = 50) -> str:
        """Truncate text if longer than max_length"""
        return text if len(text) <= max_length else text[:max_length - 3] + "..."
    
    def convert_length(self, length: int) -> str:
        """Convert length to a more readable format"""
        if length < 60:
            return f"{length}"
        elif length < 3600:
            minutes = length // 60
            seconds = length % 60
            return f"{minutes}:{seconds}"
        else:
            hours = length // 3600
            minutes = (length % 3600) // 60
            seconds = length % 60
            return f"{hours}:{minutes}:{seconds}"