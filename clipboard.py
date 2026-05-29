"""Lectura y escritura del clipboard, simulando Ctrl+C / Ctrl+V."""

import time

import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()

# Modificadores que el usuario puede tener presionados al disparar el hotkey
# (Ctrl+Shift+...). Los soltamos antes de inyectar nuestra propia combinación
# para no contaminarla.
_MODIFIERS = (Key.ctrl_l, Key.ctrl_r, Key.shift_l, Key.shift_r, Key.alt_l, Key.alt_r)


def _release_modifiers() -> None:
    for key in _MODIFIERS:
        try:
            _keyboard.release(key)
        except Exception:
            pass


def _send_ctrl(char: str) -> None:
    """Inyecta Ctrl+<char> de forma limpia (sin otros modificadores)."""
    _release_modifiers()
    time.sleep(0.05)
    with _keyboard.pressed(Key.ctrl):
        _keyboard.press(char)
        _keyboard.release(char)


def copy_selection(timeout: float = 0.4) -> str:
    """Copia el texto seleccionado (Ctrl+C) y devuelve su contenido.

    Limpia el clipboard antes para poder detectar contenido nuevo; si no se
    copió nada (no había selección) restaura el contenido previo.
    """
    try:
        previous = pyperclip.paste()
    except Exception:
        previous = ""

    try:
        pyperclip.copy("")
    except Exception:
        pass

    _send_ctrl("c")

    deadline = time.time() + timeout
    text = ""
    while time.time() < deadline:
        time.sleep(0.03)
        try:
            text = pyperclip.paste()
        except Exception:
            text = ""
        if text:
            break

    if not text:
        # No había selección: no rompemos lo que el usuario tenía copiado.
        try:
            pyperclip.copy(previous)
        except Exception:
            pass
        return ""

    return text.strip()


def paste_text(text: str) -> None:
    """Escribe `text` en el clipboard y simula Ctrl+V para pegarlo."""
    pyperclip.copy(text)
    time.sleep(0.05)
    _send_ctrl("v")
