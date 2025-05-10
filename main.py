import os
from textual.app import App, ComposeResult
from textual.containers import (
    HorizontalScroll,
    ScrollableContainer,
    Horizontal, 
    VerticalScroll
)
from textual.binding import Binding
from textual.widgets import (
    Header, 
    Footer, 
    Input,
    Select,
    Static,
    ContentSwitcher,
    OptionList
)

from dotenv import load_dotenv

load_dotenv()

class SearchBar(Static):
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Input(placeholder="Search...", id="search-input"),
            Select(
                options=[
                    ("Option 1", "opt1"),
                    ("Option 2", "opt2"),
                    ("Option 3", "opt3"),
                ],
                id="search-options"
            ),
            classes="search-container"
        )

class Sidebar(Static):
    def compose(self) -> ComposeResult:
        yield OptionList(
            "Dashboard",
            "Settings",
            "Profile",
            "Help",
            id="sidebar-options"
        )

class MainContent(Static):
    def compose(self) -> ComposeResult:
        yield ScrollableContainer(
            Static("Main content area", id="content-area"),
            id="main-grid"
        )

class Hanazawa(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="f", action="focus_search", description="Focus Search"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(name=os.getenv('APP_NAME', 'Hanazawa'), show_clock=True, id="header", classes="header")
        yield SearchBar(id="search-bar")
        yield Horizontal(
            Sidebar(id="sidebar", classes="sidebar"),
            MainContent(id="main-content"),
            id="app-container"
        )
        yield Footer()

if __name__ == "__main__":
    app = Hanazawa()
    app.run()