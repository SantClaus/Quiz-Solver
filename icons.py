"""Íconos del system tray generados programáticamente con Pillow.

Círculos de colores simples para cada estado, evitando assets binarios.
"""

from PIL import Image, ImageDraw

_SIZE = 64
_PAD = 8


def _circle(color: tuple[int, int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (_SIZE, _SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([_PAD, _PAD, _SIZE - _PAD, _SIZE - _PAD], fill=color)
    return img


def active() -> Image.Image:
    """Verde: hotkeys activos, idle."""
    return _circle((46, 204, 113, 255))


def inactive() -> Image.Image:
    """Gris: hotkeys desactivados."""
    return _circle((127, 140, 141, 255))


def loading() -> Image.Image:
    """Amarillo: esperando respuesta de la API."""
    return _circle((241, 196, 15, 255))


def ready() -> Image.Image:
    """Azul con check: respuesta lista para pegar."""
    img = _circle((52, 152, 219, 255))
    draw = ImageDraw.Draw(img)
    draw.line([(20, 33), (29, 43), (45, 22)], fill=(255, 255, 255, 255), width=6)
    return img
