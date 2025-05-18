import os
import logging
import time
from textual import work
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    Static, 
    LoadingIndicator, 
    DataTable, 
    Input,
    Header,
    Footer,
    )
from textual.message import Message
from textual.events import Click
from templates import BaseTemplate
import pyfiglet

# Set up logging
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=f"""../logs/dev-{time.strftime("%Y-%m-%d")}.log""",
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Radio Page
class RadioPage(BaseTemplate):
    CSS_PATH = "../assets/css/radio_page/main.tcss"

    def __init__(self) -> None:
        super().__init__(subtitle="Radio Page")

    def compose(self) -> ComposeResult:
        yield Header(
            name=os.getenv('APP_NAME', ''),
            show_clock=True,
            id="radio-header"
        )
        
        # Main content grid
        with Container(id="radio-app"):
            pass
        
        yield Footer(id="radio-footer")