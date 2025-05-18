import os
from textual.app import ComposeResult
from textual.containers import (
    Container,
    VerticalScroll,
    Horizontal
)
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button
)

from utils import pages

class BaseTemplate(Screen):
    """Base template for all pages"""
    CSS_PATH = "../assets/css/styles.tcss"
    
    def __init__(self, subtitle: str = "") -> None:
        super().__init__()
        self.subtitle = subtitle
        self.pages = pages.get_menu_pages()

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True
        )
        
        # Main content grid
        with Container(id="app-grid", classes="app-grid"):
            with VerticalScroll(id="left-pane", classes="left-pane"):
                yield from self.compose_left_pane()
            with Horizontal(id="main-right", classes="main-right"):
                yield from self.compose_main_content()
        
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = self.subtitle

    def compose_left_pane(self) -> ComposeResult:
        """Override this method to customize left pane content"""
        yield Static("Menu", id="left-pane-title", classes="left-pane-title")

        for page in self.pages:
            yield Button(page['title'], id=f"nav-{page['name'].lower()}", classes="nav-button")

    def compose_main_content(self) -> ComposeResult:
        """Override this method to customize main content"""
        yield Static("Main Content")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button clicks"""
        button_id = event.button.id
        if button_id and button_id.startswith("nav-"):
            page_name = button_id[4:]
            page = next((p for p in self.pages if p['name'].lower() == page_name), None)
            if page:
                self.app.switch_mode(page['name'])