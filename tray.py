"""Ícono en system tray con pystray."""

import pystray

import icons


class Tray:
    def __init__(self, on_toggle, on_quit, is_enabled) -> None:
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._is_enabled = is_enabled
        self.icon = pystray.Icon(
            "ai-clipboard",
            icons.active(),
            "AI Clipboard",
            menu=self._build_menu(),
        )

    def _build_menu(self) -> "pystray.Menu":
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: (
                    "✓ Hotkeys activos"
                    if self._is_enabled()
                    else "✗ Hotkeys desactivados"
                ),
                self._toggle,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", self._quit),
        )

    def _toggle(self, icon, item) -> None:
        self._on_toggle()
        icon.update_menu()

    def _quit(self, icon, item) -> None:
        self._on_quit()
        icon.stop()

    def set_state(self, image, tooltip: str) -> None:
        """Actualiza el ícono y el tooltip. Seguro desde cualquier thread."""
        self.icon.icon = image
        self.icon.title = tooltip

    def run(self) -> None:
        """Arranca el loop del tray. Bloquea el thread actual."""
        self.icon.run()

    def run_detached(self) -> None:
        """Arranca el tray sin bloquear (su loop corre aparte).

        En macOS lo usamos para liberar el thread principal: Cocoa exige que
        Tkinter (el overlay) viva ahí, así que el tray queda "detached".
        """
        self.icon.run_detached()
