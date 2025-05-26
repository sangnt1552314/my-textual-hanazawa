import os
import logging
import asyncio
from rich.text import Text
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
    Rule,
    DataTable,
)
from textual.events import Click
from utils.youtube import YoutubeVideoService
from utils.audio_player import YoutubeAudioPlayer, VLCPlayer
from textual import work

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
            yield Static(self.video["title"], classes="youtube_result_title")
            yield Static(f"{self.video["channel_title"]}", classes="youtube_result_metadata")

class YoutubePage(BaseTemplate):
    CSS_PATH = "../assets/css/youtube_page/main.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "switch_mode('radio')", "Radio"),
    ]

    AUTO_FOCUS = None

    def __init__(self) -> None:
        super().__init__(subtitle="Youtube")
        self.youtube_video_service = YoutubeVideoService()
        self.youtube_audio_player = YoutubeAudioPlayer()
        self.youtube_video_result_view_type = 'datatable' # 'container' or 'datatable'
        self.playing_url = None
        self.playing_video_id = None
        self.current_duration = 0
        self.current_time = 0
        self.timer_running = False

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
                        if self.youtube_video_result_view_type == 'container':
                            with Grid(id="youtube_container_type_results"):
                                yield Static("Hi, there is nothing right now!!!")
                        else:
                            yield DataTable(id="youtube_datatable_type_results")

        with Container(id="youtube_player_bar"):
            with Horizontal(id="youtube_player_info"):
                yield Label("0:00 / 0:00", id="youtube_player_timer")
                yield Label("Now Playing: ", id="youtube_player_status")
                yield Label("No Video Selected", id="youtube_current_video")
            with Horizontal(id="youtube_player_controls"):
                yield Button("P", id="youtube_play_pause_button", variant="primary", disabled=True)

        yield Footer()

    def on_mount(self) -> None:
        result_datatable = self.query_one("#youtube_datatable_type_results", DataTable)
        result_datatable.cursor_type = "row"
        result_datatable.add_column("Title", width=40)
        result_datatable.add_column("Channel", width=20)

    def on_input_submitted(self, event: Input.Submitted):
        """Handle search input submission"""
        self.clean_container_results()

        search_input = self.query_one("#youtube_search_input", Input)
        search_query = search_input.value.strip()

        if search_query:
            videos = self.youtube_video_service.search_video(query=search_query, max_results=10, filters={"order": "viewCount"})

            if not videos:
                search_input.placeholder = "No results found"
                search_input.value = ""
                return

            # Clear existing results
            container_id = "#youtube_container_type_results" if self.youtube_video_result_view_type == 'container' else "#youtube_datatable_type_results"
            container_type = Grid if self.youtube_video_result_view_type == 'container' else DataTable
            container = self.query_one(container_id, container_type)
            container.remove_children()

            for video in videos:
                if self.youtube_video_result_view_type == 'container':
                    video_container = YoutubeVideoContainer(video=video)
                    container.mount(video_container)

                if self.youtube_video_result_view_type == 'datatable':
                    styled_row = [
                        Text(self.truncate_text(video["title"], 50), style="italic #03AC13", justify="left"),
                        Text(self.truncate_text(video["channel_title"], 20), style="italic #03AC13", justify="left")
                    ]
                    container.add_row(*styled_row, key=video["video_id"])

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """Handle selection of list view items"""
        selected_item = message.item

        if selected_item.id == "youtube_left_pane_list_item_clear":
            self.clear_search_results()

    def on_click(self, event) -> None:
        if isinstance(event, Click):
            self.lose_search_input_focus(event)

        if isinstance(event, YoutubeVideoContainer):
            pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the DataTable"""
        result_table = self.query_one("#youtube_datatable_type_results", DataTable)
        if result_table is not None and event.row_key is not None:
            row = result_table.get_row_at(event.cursor_row)
            video_title = row[0].plain
            video_id = event.row_key.value
            audio_url = self.youtube_video_service.get_video_audio_url(video_id=video_id)

            if audio_url:
                self.playing_url = audio_url
                play_pause_button = self.query_one("#youtube_play_pause_button", Button)
                play_pause_button.disabled = False
                play_pause_button.label = "S"
                self.query_one("#youtube_current_video", Label).update(f"{video_title}")

                # Get video duration
                self.current_duration = self.youtube_video_service.get_video_duration(video_id)
                self.current_time = 0
                self.update_timer_display()

                # Play the audio
                self.playing_video_id = video_id
                self.youtube_audio_player.play_stream_url(audio_url)
                self.start_timer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "youtube_play_pause_button":
            if self.youtube_audio_player.is_playing:
                self.youtube_audio_player.pause()
                event.button.label = "P"
                self.timer_running = False
            elif self.youtube_audio_player.is_paused:
                self.youtube_audio_player.resume()
                event.button.label = "S"
                self.start_timer()
            else:
                self.youtube_audio_player.play_stream_url(self.playing_url)
                event.button.label = "S"
                self.start_timer()

    def clear_search_results(self) -> None:
        """Clear search results"""
        self.playing_url = None
        self.stop_timer()

        search_input = self.query_one("#youtube_search_input", Input)
        search_input.value = ""
        search_input.placeholder = "Search..."

        self.clean_container_results()

    def clean_container_results(self) -> None:
        container_id = "#youtube_container_type_results" if self.youtube_video_result_view_type == 'container' else "#youtube_datatable_type_results"
        container_type = Grid if self.youtube_video_result_view_type == 'container' else DataTable
        container = self.query_one(container_id, container_type)

        if isinstance(container, DataTable):
            container.clear()
        elif isinstance(container, Grid):
            container.remove_children()

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

    @work(exclusive=True)
    async def update_timer(self) -> None:
        """Update the timer display every second"""
        while self.timer_running and self.current_time < self.current_duration:
            await asyncio.sleep(1)
            if isinstance(self.youtube_audio_player.current_player, VLCPlayer):
                self.current_time = self.youtube_audio_player.get_current_time()
            else:
                self.current_time += 1
            self.update_timer_display()

    def start_timer(self) -> None:
        """Start the timer"""
        self.timer_running = True
        self.update_timer()

    def stop_timer(self) -> None:
        """Stop the timer"""
        self.timer_running = False
        self.current_time = 0
        self.update_timer_display()

    def update_timer_display(self) -> None:
        """Update the timer display"""
        current = self.format_time(self.current_time)
        total = self.format_time(self.current_duration)
        self.query_one("#youtube_player_timer", Label).update(f"{current} / {total}")

    def format_time(self, seconds: int) -> str:
        """Format seconds into MM:SS or HH:MM:SS"""
        if seconds < 3600:  # Less than an hour
            return f"{seconds // 60}:{seconds % 60:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"