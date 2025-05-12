import os
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    Static, 
)
from templates import BaseTemplate
import pyfiglet 

class HomePage(BaseTemplate):
    def __init__(self) -> None:
        super().__init__(subtitle="Home Page")

    def compose_main_content(self) -> ComposeResult:
        with Container(id="main-right", classes="main-right"):
            # Create a banner using pyfiglet
            banner = pyfiglet.figlet_format(os.getenv('APP_NAME', ''), font="slant", width=100)
            yield Static(banner, id="main-right-title", classes="main-right-title")

            # create table of music stations
            with Container(id="main-right-body", classes="main-right-body"):
                yield Static("Now Playing Stations", id="main-right-body-title", classes="main-right-body-title")