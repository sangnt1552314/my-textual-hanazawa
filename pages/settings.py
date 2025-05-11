from textual.app import ComposeResult
from textual.widgets import Static
from templates import BaseTemplate

class SettingsPage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Settings Page")

    def compose_main_content(self) -> ComposeResult:
        yield Static("TBU", id="main-right-text")