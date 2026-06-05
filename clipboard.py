"""Lectura y escritura del clipboard.

Con los hotkeys mapeados a Ctrl+C / Ctrl+V nativos ya NO simulamos esas
combinaciones: lo hace el propio atajo del usuario y simularlas re-dispararía
el hotkey (loop infinito). Solo leemos lo que el usuario copió y escribimos la
respuesta de Claude para que su Ctrl+V la pegue.
"""

import time

import pyperclip
from PIL import Image, ImageGrab
from pynput.keyboard import Controller, Key

# Cuánto esperar a que el SO termine de copiar la selección tras el Ctrl+C
# real del usuario antes de leer el clipboard.
_COPY_SETTLE = 0.15

_keyboard = Controller()

# Modificadores que el usuario puede tener presionados al disparar Ctrl+J.
# Los soltamos antes de inyectar nuestro Ctrl+C para no contaminarlo.
_MODIFIERS = (Key.ctrl_l, Key.ctrl_r, Key.shift_l, Key.shift_r, Key.alt_l, Key.alt_r)


def read_selection() -> str:
    """Devuelve el texto que el usuario acaba de copiar con su Ctrl+C."""
    time.sleep(_COPY_SETTLE)
    try:
        text = pyperclip.paste()
    except Exception:
        return ""
    return text.strip()


def _release_modifiers() -> None:
    for key in _MODIFIERS:
        try:
            _keyboard.release(key)
        except Exception:
            pass


def copy_selection(timeout: float = 0.4) -> str:
    """Simula Ctrl+C para copiar la selección y devuelve el texto.

    Lo usa Ctrl+J, que (a diferencia de Ctrl+C) no copia por sí solo. Limpia el
    clipboard antes para detectar contenido nuevo; si no se copió nada (no había
    selección) restaura lo que el usuario tenía.
    """
    try:
        previous = pyperclip.paste()
    except Exception:
        previous = ""

    try:
        pyperclip.copy("")
    except Exception:
        pass

    _release_modifiers()
    time.sleep(0.05)
    with _keyboard.pressed(Key.ctrl):
        _keyboard.press("c")
        _keyboard.release("c")

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
        try:
            pyperclip.copy(previous)
        except Exception:
            pass
        return ""

    return text.strip()


def grab_screen() -> "Image.Image | None":
    """Captura toda la pantalla a memoria, sin tocar el clipboard ni notificar.

    A diferencia de ImprPant / Win+Shift+S (que dejan la imagen en el clipboard y
    pueden disparar la Herramienta de Recortes), esto lee los píxeles directo con
    `ImageGrab.grab`: silencioso, invisible y sin pisar lo que el usuario copió.
    `all_screens=True` abarca todos los monitores.
    """
    try:
        return ImageGrab.grab(all_screens=True)
    except Exception:
        return None


def _grab_image() -> "Image.Image | None":
    """Imagen actual del clipboard, o None si no hay ninguna."""
    try:
        data = ImageGrab.grabclipboard()
    except Exception:
        data = None
    return data if isinstance(data, Image.Image) else None


def _signature(image: "Image.Image") -> tuple:
    """Firma barata para distinguir una imagen de otra."""
    return (image.size, hash(image.tobytes()))


def read_image(timeout: float = 2.5, wait_new: bool = False) -> "Image.Image | None":
    """Devuelve un screenshot del clipboard, o None si no aparece a tiempo.

    - `ImprPant` deja la captura al instante: `wait_new=False` la lee enseguida.
    - `Win+Shift+S` abre el recortador y la imagen recién aparece cuando el
      usuario termina de seleccionar. Con `wait_new=True` ignoramos la imagen que
      ya estuviera en el clipboard y esperamos a que aparezca una distinta.
    """
    baseline = None
    if wait_new:
        current = _grab_image()
        if current is not None:
            baseline = _signature(current)

    deadline = time.time() + timeout
    while True:
        img = _grab_image()
        if img is not None and (not wait_new or _signature(img) != baseline):
            return img
        if time.time() >= deadline:
            return None
        time.sleep(0.05)


def set_clipboard(text: str, ensure_for: float = 3.0) -> None:
    """Escribe `text` en el clipboard insistiendo hasta confirmar que quedó.

    Tras un screenshot, la Herramienta de Recortes puede tener el clipboard
    tomado (y `pyperclip.copy` falla) o re-escribir la imagen, dejando nuestra
    respuesta afuera. Reintentamos hasta leer de vuelta nuestro texto o agotar
    `ensure_for` segundos. Cortamos apenas el texto está, así que no peleamos con
    lo que el usuario copie después.
    """
    deadline = time.time() + ensure_for
    while True:
        try:
            pyperclip.copy(text)
        except Exception:
            pass
        try:
            current = pyperclip.paste()
        except Exception:
            current = None
        if current == text or time.time() >= deadline:
            return
        time.sleep(0.1)
