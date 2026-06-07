"""Ícono en system tray con pystray."""

import functools

import pystray

import icons


class Tray:
    def __init__(self, groups, on_toggle, on_quit, is_enabled) -> None:
        # groups: lista de (key, label). Cada uno es un grupo de hotkeys con su
        # propio toggle en el menú (captura / texto / recorte).
        self._groups = groups
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
        items = []
        for key, label in self._groups:
            items.append(
                pystray.MenuItem(
                    # key/label por default-arg para capturar el valor del loop.
                    lambda item, key=key, label=label: (
                        f"✓ {label}"
                        if self._is_enabled(key)
                        else f"✗ {label}"
                    ),
                    # functools.partial (no __code__) en vez de lambda: pystray
                    # rechaza acciones con co_argcount > 2, y un lambda con
                    # `key=key` cuenta 3 args. partial liga la key y deja que
                    # pystray invoque con (icon, item).
                    functools.partial(self._toggle, key),
                )
            )
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Salir", self._quit))
        return pystray.Menu(*items)

    def _toggle(self, key, icon, item) -> None:
        # partial liga `key`; pystray pasa (icon, item) al invocar.
        self._on_toggle(key)
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
