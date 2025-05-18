from textual.app import App
from textual.binding import Binding
from pages import (
    RadioPage,
    SettingsPage,
    BasePage,
)

class HanazawaApp(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="r", action="switch_mode('radio')", description="Radio"),
        Binding(key="s", action="switch_mode('settings')", description="Settings"),
    ]

    MODES = {
        "base": BasePage,
        "radio": RadioPage,
        "settings": SettingsPage
    }

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None:
        self.switch_mode("radio")