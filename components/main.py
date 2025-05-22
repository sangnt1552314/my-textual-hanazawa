from textual.app import App
from textual.binding import Binding
from pages import (
    RadioPage,
    SettingsPage,
    BasePage,
    YoutubePage
)

class HanazawaApp(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="r", action="switch_mode('radio')", description="Radio"),
        Binding(key="y", action="switch_mode('youtube')", description="Youtube"),
        Binding(key="ctrl+s", action="switch_mode('settings')", description="Settings"),
    ]

    MODES = {
        "base": BasePage,
        "radio": RadioPage,
        "youtube": YoutubePage,
        "settings": SettingsPage
    }

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None:
        self.switch_mode("base")