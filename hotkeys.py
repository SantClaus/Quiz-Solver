"""Registro y manejo de hotkeys globales con pynput."""

from pynput import keyboard


class Hotkeys:
    """Escucha Ctrl+Shift+C y Ctrl+Shift+V de forma global.

    Los callbacks corren en el thread del listener, así que deben ser livianos
    (delegar el trabajo pesado a otro thread).
    """

    def __init__(self, on_capture, on_paste) -> None:
        self._listener = keyboard.GlobalHotKeys(
            {
                "<ctrl>+<shift>+c": on_capture,
                "<ctrl>+<shift>+v": on_paste,
            }
        )

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()
