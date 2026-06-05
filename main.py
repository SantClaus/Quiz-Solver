"""Entry point: arranca el tray y el listener de hotkeys globales.

Coordina los estados del sistema (activo / procesando / respuesta lista /
desactivado) y la comunicación entre los hotkeys, el clipboard y la API.
"""

import sys
import threading

import config
import icons
from ai_client import AIClient
from clipboard import (
    copy_selection,
    grab_screen,
    read_image,
    read_selection,
    set_clipboard,
)
from hotkeys import Hotkeys
from overlay import Overlay
from tray import Tray

# Cuánto mostrar el ícono "ready" antes de volver a "active".
READY_DURATION = 2.5


class App:
    def __init__(self) -> None:
        config.validate()
        self._client = AIClient()

        self._enabled = True
        self._response: str | None = None
        self._last_answer: str | None = None
        self._cancel_event: threading.Event | None = None
        self._ready_timer: threading.Timer | None = None
        self._lock = threading.Lock()
        # Ignora el hotkey de Ctrl+C que dispara nuestro propio Ctrl+J simulado.
        self._suppress_capture = False

        self._tray = Tray(self.toggle_enabled, self.quit, lambda: self._enabled)
        self._hotkeys = Hotkeys(
            self.on_capture,
            self.on_capture_alt,
            self.on_paste,
            self.on_screenshot,
            self.on_snip,
            self.on_fullscreen,
        )
        # Cuadradito junto al cursor con la última respuesta mientras Ctrl+9.
        self._overlay = Overlay(
            should_show=lambda: self._enabled and self._hotkeys.overlay_held(),
            get_text=lambda: self._last_answer,
        )

    # --- Transiciones de ícono ------------------------------------------
    def _set_active(self) -> None:
        self._tray.set_state(icons.active(), "AI Clipboard — activo")

    def _set_loading(self) -> None:
        self._tray.set_state(icons.loading(), "AI Clipboard — consultando…")

    def _set_ready(self) -> None:
        self._tray.set_state(
            icons.ready(), "AI Clipboard — respuesta lista (Ctrl+V)"
        )

    def _set_disabled(self) -> None:
        self._tray.set_state(icons.inactive(), "AI Clipboard — desactivado")

    def _set_error(self, exc: Exception) -> None:
        self._tray.set_state(icons.error(), f"AI Clipboard — error: {exc}")

    # --- Captura de texto (Ctrl+C / Ctrl+J) -----------------------------
    def on_capture(self) -> None:
        # El Ctrl+C que simulamos para Ctrl+J vuelve a entrar acá: lo ignoramos.
        if not self._enabled or self._suppress_capture:
            return
        # El callback corre en el thread del listener: delegamos el trabajo.
        threading.Thread(target=self._capture_flow, daemon=True).start()

    def on_capture_alt(self) -> None:
        # Ctrl+J: igual que Ctrl+C pero con el prompt alternativo.
        if not self._enabled:
            return
        threading.Thread(
            target=self._capture_flow, kwargs={"justify": True}, daemon=True
        ).start()

    def _capture_flow(self, justify: bool = False) -> None:
        if justify:
            # Ctrl+J no copia solo: simulamos Ctrl+C ignorando nuestro hotkey.
            self._suppress_capture = True
            try:
                question = copy_selection()
            finally:
                self._suppress_capture = False
        else:
            question = read_selection()

        if not question:
            return

        # El Ctrl+V deja nuestra respuesta en el clipboard; si el usuario hace
        # Ctrl+C sin selección, leeríamos esa misma respuesta. La ignoramos para
        # no reenviarla a Claude.
        with self._lock:
            if question == self._last_answer:
                return

        system = config.SYSTEM_PROMPT_2 if justify else config.SYSTEM_PROMPT
        self._ask(lambda cancel: self._client.ask(question, cancel, system=system))

    # --- Screenshot (ImprPant / Win+Shift+S) ----------------------------
    def on_screenshot(self, justify: bool = False) -> None:
        # ImprPant: la captura ya está en el clipboard.
        if not self._enabled:
            return
        threading.Thread(
            target=self._screenshot_flow,
            kwargs={"wait_new": False, "justify": justify},
            daemon=True,
        ).start()

    def on_snip(self, justify: bool = False) -> None:
        # Win+Shift+S: hay que esperar a que el usuario termine de recortar.
        if not self._enabled:
            return
        threading.Thread(
            target=self._screenshot_flow,
            kwargs={"wait_new": True, "justify": justify},
            daemon=True,
        ).start()

    def on_fullscreen(self) -> None:
        # Ctrl/Cmd+0: captura toda la pantalla a memoria, sin notificación.
        if not self._enabled:
            return
        threading.Thread(target=self._fullscreen_flow, daemon=True).start()

    def _fullscreen_flow(self) -> None:
        image = grab_screen()
        if image is None:
            return
        self._ask(
            lambda cancel: self._client.ask_image(
                image, cancel, system=config.SCREEN_PROMPT
            )
        )

    def _screenshot_flow(self, wait_new: bool, justify: bool = False) -> None:
        # Margen amplio: ImprPant puede estar configurado para abrir la
        # Herramienta de Recortes (como Win+Shift+S), y entonces la imagen recién
        # aparece cuando el usuario termina de seleccionar la zona.
        image = read_image(timeout=15.0, wait_new=wait_new)
        if image is None:
            return
        # Con la J sostenida usamos el prompt alternativo (SYSTEM_PROMPT_2).
        system = config.SYSTEM_PROMPT_2 if justify else config.SYSTEM_PROMPT
        self._ask(lambda cancel: self._client.ask_image(image, cancel, system=system))

    # --- Consulta genérica (texto o imagen) -----------------------------
    def _ask(self, call) -> None:
        """Corre `call(cancel_event)` mostrando los estados del ícono.

        `call` hace la llamada a Claude (texto o imagen) y devuelve la respuesta.
        """
        # Cancela cualquier llamada en curso y crea un token nuevo.
        with self._lock:
            if self._cancel_event is not None:
                self._cancel_event.set()
            if self._ready_timer is not None:
                self._ready_timer.cancel()
            cancel = threading.Event()
            self._cancel_event = cancel

        self._set_loading()

        try:
            answer = call(cancel)
        except Exception as exc:  # noqa: BLE001 - feedback al usuario via tooltip
            if not cancel.is_set():
                self._set_error(exc)
                self._start_ready_timer()  # rojo unos segundos y vuelve a activo
            return

        # Una nueva captura pudo haber reemplazado a esta. Tratamos la respuesta
        # vacía como "sin respuesta" para no mostrar "listo" y pegar nada.
        if cancel.is_set() or not answer:
            return

        with self._lock:
            self._response = answer
            self._last_answer = answer
        # Dejamos la respuesta en el clipboard para que el Ctrl+V nativo la pegue.
        set_clipboard(answer)
        # Se queda en "ready" (verde oscuro) hasta que el usuario pegue: no hay
        # timer que lo devuelva a "active" solo.
        self._set_ready()

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

    # --- Pegado (Ctrl+V) ------------------------------------------------
    def on_paste(self) -> None:
        if not self._enabled:
            return
        threading.Thread(target=self._paste_flow, daemon=True).start()

    def _paste_flow(self) -> None:
        # El Ctrl+V nativo del usuario ya pega la respuesta (la dejamos en el
        # clipboard al recibirla). Acá solo limpiamos el estado y volvemos al
        # ícono activo. No simulamos Ctrl+V: re-dispararía este hotkey.
        with self._lock:
            had_response = self._response is not None
            self._response = None
        if had_response and self._enabled:
            if self._ready_timer is not None:
                self._ready_timer.cancel()
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
        self._overlay.stop()

    # --- Arranque -------------------------------------------------------
    def run(self) -> None:
        self._hotkeys.start()
        if config.IS_MAC:
            # Cocoa exige que Tkinter (el overlay) viva en el thread principal,
            # así que el tray va "detached" y el overlay toma el thread principal.
            self._tray.run_detached()
            self._set_active()
            self._overlay.run_main()  # bloquea con el mainloop de Tk
        else:
            # En Windows el overlay corre en su propio thread y el tray bloquea.
            self._overlay.start()
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
