"""Entry point: arranca el tray y el listener de hotkeys globales.

Coordina los estados del sistema (activo / procesando / respuesta lista /
desactivado) y la comunicación entre los hotkeys, el clipboard y la API.
"""

import sys
import threading

import config
import icons
from ai_client import AIClient
from clipboard import copy_selection, paste_text
from hotkeys import Hotkeys
from tray import Tray

# Cuánto mostrar el ícono "ready" antes de volver a "active".
READY_DURATION = 2.5


class App:
    def __init__(self) -> None:
        config.validate()
        self._client = AIClient()

        self._enabled = True
        self._response: str | None = None
        self._cancel_event: threading.Event | None = None
        self._ready_timer: threading.Timer | None = None
        self._lock = threading.Lock()

        self._tray = Tray(self.toggle_enabled, self.quit, lambda: self._enabled)
        self._hotkeys = Hotkeys(self.on_capture, self.on_paste)

    # --- Transiciones de ícono ------------------------------------------
    def _set_active(self) -> None:
        self._tray.set_state(icons.active(), "AI Clipboard — activo")

    def _set_loading(self) -> None:
        self._tray.set_state(icons.loading(), "AI Clipboard — consultando…")

    def _set_ready(self) -> None:
        self._tray.set_state(
            icons.ready(), "AI Clipboard — respuesta lista (Ctrl+Shift+V)"
        )

    def _set_disabled(self) -> None:
        self._tray.set_state(icons.inactive(), "AI Clipboard — desactivado")

    # --- Captura (Ctrl+Shift+C) -----------------------------------------
    def on_capture(self) -> None:
        if not self._enabled:
            return
        # El callback corre en el thread del listener: delegamos el trabajo.
        threading.Thread(target=self._capture_flow, daemon=True).start()

    def _capture_flow(self) -> None:
        # Cancela cualquier llamada en curso y crea un token nuevo.
        with self._lock:
            if self._cancel_event is not None:
                self._cancel_event.set()
            if self._ready_timer is not None:
                self._ready_timer.cancel()
            cancel = threading.Event()
            self._cancel_event = cancel

        question = copy_selection()
        if not question:
            return

        self._set_loading()

        try:
            answer = self._client.ask(question, cancel)
        except Exception as exc:  # noqa: BLE001 - feedback al usuario via tooltip
            if not cancel.is_set():
                self._tray.set_state(
                    icons.active(), f"AI Clipboard — error: {exc}"
                )
            return

        # Una nueva captura pudo haber reemplazado a esta.
        if cancel.is_set() or answer is None:
            return

        with self._lock:
            self._response = answer
        self._set_ready()
        self._start_ready_timer()

    def _start_ready_timer(self) -> None:
        with self._lock:
            if self._ready_timer is not None:
                self._ready_timer.cancel()
            timer = threading.Timer(READY_DURATION, self._revert_to_active)
            self._ready_timer = timer
        timer.start()

    def _revert_to_active(self) -> None:
        if self._enabled:
            self._set_active()

    # --- Pegado (Ctrl+Shift+V) ------------------------------------------
    def on_paste(self) -> None:
        if not self._enabled:
            return
        threading.Thread(target=self._paste_flow, daemon=True).start()

    def _paste_flow(self) -> None:
        with self._lock:
            response = self._response
            self._response = None
        if not response:
            return
        paste_text(response)
        if self._enabled:
            self._set_active()

    # --- Toggle / salir -------------------------------------------------
    def toggle_enabled(self) -> None:
        self._enabled = not self._enabled
        if self._enabled:
            self._set_active()
        else:
            with self._lock:
                if self._cancel_event is not None:
                    self._cancel_event.set()
            self._set_disabled()

    def quit(self) -> None:
        self._hotkeys.stop()

    # --- Arranque -------------------------------------------------------
    def run(self) -> None:
        self._hotkeys.start()
        self._set_active()
        self._tray.run()  # bloquea hasta que se cierra el tray


def main() -> None:
    try:
        app = App()
    except Exception as exc:  # noqa: BLE001
        print(f"Error de configuración: {exc}", file=sys.stderr)
        sys.exit(1)
    app.run()


if __name__ == "__main__":
    main()
