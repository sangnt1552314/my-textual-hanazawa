import os
import logging
from templates import BaseTemplate
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
    VerticalScroll
)
from textual.widgets import (
    Input,
    Header,
    Footer,
    Label,
    Button,
    ListView,
    ListItem,
    DataTable,
)
from textual.events import Click

logging.basicConfig(
    filename=f"dev.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='w'  # a = append, w = overwrite
)
logger = logging.getLogger(__name__)


class YoutubePage(BaseTemplate):
    CSS_PATH = "../assets/css/youtube_page/main.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "switch_mode('radio')", "Radio"),
    ]

    def __init__(self) -> None:
        super().__init__(subtitle="Youtube")

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
                    id="youtube_left_pane_list_view"
                )
                    

            with Horizontal(id="youtube_main_right"):
                with Vertical(id="youtube_search_container"):
                    yield Input(placeholder="Search...", 
                        id="youtube_search_input", 
                        tooltip="TBU")
                
                    yield DataTable(id="youtube_search_results")

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#youtube_search_results", DataTable)
        table.add_columns("Title", "Channel", "Duration", "Views")

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """Handle selection of list view items"""
        selected_item = message.item
    
    def on_click(self, event) -> None:
        if isinstance(event, Click):
            self._lose_search_input_focus(event)

    def _lose_search_input_focus(self, event: Click) -> None:
        search_input = self.query_one("#youtube_search_input", Input)
        
        if event.widget.id != "youtube_search_input":
            search_input.blur()
            self.set_focus(event.widget)
