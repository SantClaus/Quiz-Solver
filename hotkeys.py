"""Registro y manejo de hotkeys globales con pynput.

Cross-platform: el modificador primario es Ctrl en Windows/Linux y Cmd (⌘) en
macOS (`config.PRIMARY_MOD`).

- **Ctrl/Cmd + 0** → captura toda la pantalla y la manda a Claude (hotkey propio).
- **Ctrl/Cmd + 9** (sostenido) → muestra el overlay con la última respuesta; no es
  un hotkey propio, lo detecta el listener de tracking vía `overlay_held()`.

En **Windows** además se registran los atajos originales (Ctrl+C/J/V de texto,
Win+Shift+S de recorte) y el screenshot por Print Screen. En **macOS** esos no se
portan (Cmd+C/V son el copiar/pegar nativo y no hay ImprPant), así que solo viven
Cmd+0 y Cmd+9.
"""

import time

from pynput import keyboard

import config

# Virtual-key de la tecla J (0x4A). Usamos el vk en vez del carácter porque no
# cambia con Shift (Win+Shift+S+J manda 'J', no 'j'). Solo se usa en Windows.
_VK_J = ord("J")
# Virtual-key de Print Screen (VK_SNAPSHOT, 0x2C). Solo en Windows.
_VK_PRINT_SCREEN = 0x2C

# Virtual-key de la tecla 9 y teclas del modificador primario, por plataforma.
# Ojo: el vk NO es portable — en Windows los dígitos usan el VK ASCII (9 = 0x39),
# en macOS usan el keycode de Carbon (kVK_ANSI_9 = 25).
if config.IS_MAC:
    _VK_9 = 25  # kVK_ANSI_9
    _MOD_KEYS = (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r)
else:
    _VK_9 = ord("9")  # 0x39
    _MOD_KEYS = (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)


class Hotkeys:
    """Escucha los hotkeys globales y rastrea las teclas sostenidas.

    `GlobalHotKeys` es un listener pasivo (no suprime el evento), así que el
    copiar/pegar nativo del usuario se ejecuta igual: el SO lo hace y además nos
    avisa. Por eso los callbacks de copiar/pegar NO deben volver a simular esas
    teclas (re-dispararían el hotkey y entrarían en loop).

    Print Screen es especial: en Windows manda solo el evento de *release*, no el
    de press, así que `GlobalHotKeys` (que dispara en press) nunca lo detecta. Lo
    manejamos a mano en el `on_release` del listener de tracking.

    Ese mismo listener de tracking sigue qué teclas están sostenidas: si la J está
    apretada al disparar un screenshot usamos el prompt alternativo, y mientras el
    modificador + 9 estén sostenidos `overlay_held()` devuelve True.

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
        self._mod_down = False  # modificador primario (Ctrl/Cmd) sostenido
        self._last_screenshot = 0.0  # anti-rebote para ImprPant

        mod = config.PRIMARY_MOD
        # Ctrl/Cmd+0: captura full silenciosa. Disponible en todas las plataformas.
        hotkeys_map = {f"{mod}+0": self._handle_fullscreen}
        if not config.IS_MAC:
            # En Windows mantenemos los atajos originales (en Mac chocarían con el
            # copiar/pegar nativo Cmd+C/V y no se portan).
            hotkeys_map.update(
                {
                    f"{mod}+c": on_capture,
                    # Ctrl+J: como Ctrl+C pero con el prompt alternativo.
                    f"{mod}+j": on_capture_alt,
                    f"{mod}+v": on_paste,
                    # Win+Shift+S: abre el recortador; la imagen aparece recién al
                    # terminar de seleccionar, así que esperamos una imagen nueva.
                    "<cmd>+<shift>+s": self._handle_snip,
                }
            )
        self._listener = keyboard.GlobalHotKeys(hotkeys_map)
        # Listener pasivo: rastrea teclas sostenidas, el modificador primario y el
        # release de ImprPant (que GlobalHotKeys no puede captar).
        self._tracker = keyboard.Listener(
            on_press=self._track_press, on_release=self._track_release
        )

    # --- Tracking de teclas ---------------------------------------------
    def _is_print_screen(self, key, vk) -> bool:
        return key == keyboard.Key.print_screen or vk == _VK_PRINT_SCREEN

    def _is_primary_mod(self, key) -> bool:
        return key in _MOD_KEYS

    def _fire_screenshot(self) -> None:
        # ImprPant puede llegar como press, como release, o ambos según el
        # equipo: disparamos en cualquiera con un anti-rebote para no duplicar.
        now = time.monotonic()
        if now - self._last_screenshot < 0.7:
            return
        self._last_screenshot = now
        self._on_screenshot(self._justify())

    def _track_press(self, key) -> None:
        vk = getattr(key, "vk", None)
        if vk is not None:
            self._pressed_vks.add(vk)
        if self._is_primary_mod(key):
            self._mod_down = True
        if self._is_print_screen(key, vk):
            self._fire_screenshot()

    def _track_release(self, key) -> None:
        vk = getattr(key, "vk", None)
        if vk is not None:
            self._pressed_vks.discard(vk)
        if self._is_primary_mod(key):
            self._mod_down = False
        if self._is_print_screen(key, vk):
            self._fire_screenshot()

    def _justify(self) -> bool:
        """True si la tecla J está sostenida (usar SYSTEM_PROMPT_2)."""
        return _VK_J in self._pressed_vks

    def overlay_held(self) -> bool:
        """True mientras el modificador primario + 9 estén sostenidos."""
        return self._mod_down and _VK_9 in self._pressed_vks

    def _handle_snip(self) -> None:
        self._on_snip(self._justify())

    def _handle_fullscreen(self) -> None:
        self._on_fullscreen()

    def start(self) -> None:
        self._tracker.start()
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()
        self._tracker.stop()
