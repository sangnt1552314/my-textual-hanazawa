import os
from templates import BaseTemplate
from textual.app import ComposeResult
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

class YoutubePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Youtube")

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True,
            id="radio-header"
        )
