from textual.app import ComposeResult
from textual.widgets import Static
from templates import BaseTemplate

class HomePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Home Page")

    def compose_main_content(self) -> ComposeResult:
        yield Static("Welcome to Home Page", id="main-right-text")