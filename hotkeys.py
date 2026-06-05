"""Registro y manejo de hotkeys globales con pynput."""

import time

from pynput import keyboard

# Virtual-key de la tecla J (0x4A). Usamos el vk en vez del carácter porque no
# cambia con Shift (Win+Shift+S+J manda 'J', no 'j').
_VK_J = ord("J")
# Virtual-key de la tecla 9 (0x39). Se mantiene aunque haya Ctrl apretado, por
# eso lo rastreamos por vk en vez de por carácter.
_VK_9 = ord("9")
# Virtual-key de Print Screen (VK_SNAPSHOT, 0x2C).
_VK_PRINT_SCREEN = 0x2C


class Hotkeys:
    """Escucha Ctrl+C, Ctrl+J, Ctrl+V y los screenshots (ImprPant / Win+Shift+S).

    `GlobalHotKeys` es un listener pasivo (no suprime el evento), así que el
    Ctrl+C / Ctrl+V nativo del usuario se ejecuta igual: el SO copia/pega y
    además nos avisa. Por eso los callbacks de Ctrl+C/Ctrl+V NO deben volver a
    simular esas teclas (re-dispararían el hotkey y entrarían en loop).

    Print Screen es especial: en Windows manda solo el evento de *release*, no el
    de press, así que `GlobalHotKeys` (que dispara en press) nunca lo detecta. Lo
    manejamos a mano en el `on_release` del listener de tracking.

    Ese mismo listener de tracking sigue qué teclas están sostenidas: si la J
    está apretada al disparar un screenshot (ImprPant+J / Win+Shift+S+J) usamos
    el prompt alternativo.

    Los callbacks corren en el thread del listener, así que deben ser livianos
    (delegar el trabajo pesado a otro thread).
    """

    def __init__(
        self,
        on_capture,
        on_capture_alt,
        on_paste,
        on_screenshot,
        on_snip,
        on_fullscreen,
    ) -> None:
        self._on_screenshot = on_screenshot
        self._on_snip = on_snip
        self._on_fullscreen = on_fullscreen
        self._pressed_vks: set[int] = set()
        self._ctrl_down = False  # estado de Ctrl para detectar Ctrl+9 sostenido
        self._last_screenshot = 0.0  # anti-rebote para ImprPant

        self._listener = keyboard.GlobalHotKeys(
            {
                "<ctrl>+c": on_capture,
                # Ctrl+J: como Ctrl+C pero con el prompt alternativo.
                "<ctrl>+j": on_capture_alt,
                "<ctrl>+v": on_paste,
                # Ctrl+0: screenshot de toda la pantalla a memoria (silencioso,
                # sin tocar el clipboard ni notificar).
                "<ctrl>+0": self._handle_fullscreen,
                # Win+Shift+S: abre el recortador; la imagen aparece recién al
                # terminar de seleccionar, así que esperamos una imagen nueva.
                "<cmd>+<shift>+s": self._handle_snip,
            }
        )
        # Listener pasivo: rastrea teclas sostenidas y detecta el release de
        # ImprPant (que GlobalHotKeys no puede captar).
        self._tracker = keyboard.Listener(
            on_press=self._track_press, on_release=self._track_release
        )

    # --- Tracking de teclas ---------------------------------------------
    def _is_print_screen(self, key, vk) -> bool:
        return key == keyboard.Key.print_screen or vk == _VK_PRINT_SCREEN

    def _fire_screenshot(self) -> None:
        # ImprPant puede llegar como press, como release, o ambos según el
        # equipo: disparamos en cualquiera con un anti-rebote para no duplicar.
        now = time.monotonic()
        if now - self._last_screenshot < 0.7:
            return
        self._last_screenshot = now
        self._on_screenshot(self._justify())

    def _is_ctrl(self, key) -> bool:
        return key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)

    def _track_press(self, key) -> None:
        vk = getattr(key, "vk", None)
        if vk is not None:
            self._pressed_vks.add(vk)
        if self._is_ctrl(key):
            self._ctrl_down = True
        if self._is_print_screen(key, vk):
            self._fire_screenshot()

    def _track_release(self, key) -> None:
        vk = getattr(key, "vk", None)
        if vk is not None:
            self._pressed_vks.discard(vk)
        if self._is_ctrl(key):
            self._ctrl_down = False
        if self._is_print_screen(key, vk):
            self._fire_screenshot()

    def _justify(self) -> bool:
        """True si la tecla J está sostenida (usar SYSTEM_PROMPT_2)."""
        return _VK_J in self._pressed_vks

    def overlay_held(self) -> bool:
        """True mientras Ctrl+9 estén sostenidos (mostrar el overlay)."""
        return self._ctrl_down and _VK_9 in self._pressed_vks

    def _handle_snip(self) -> None:
        self._on_snip(self._justify())

    def _handle_fullscreen(self) -> None:
        self._on_fullscreen(self._justify())

    def start(self) -> None:
        self._tracker.start()
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()
        self._tracker.stop()
