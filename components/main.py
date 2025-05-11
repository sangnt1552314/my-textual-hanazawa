from textual.app import App
from textual.binding import Binding
from pages import (
    HomePage,
    SettingsPage,
    BasePage,
)

class HanazawaApp(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="h", action="switch_mode('home')", description="Home"),
        Binding(key="s", action="switch_mode('settings')", description="Settings"),
    ]

    MODES = {
        "base": BasePage,
        "home": HomePage,
        "settings": SettingsPage
    }

    def on_mount(self) -> None:
        self.switch_mode("home")