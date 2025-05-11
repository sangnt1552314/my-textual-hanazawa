from textual.app import ComposeResult
from textual.widgets import Static
from templates import BaseTemplate

class BasePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Base Page")