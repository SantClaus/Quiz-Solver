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
    """Verde claro: hotkeys activos, idle (nada copiado todavía)."""
    return _circle((144, 238, 144, 255))


def inactive() -> Image.Image:
    """Gris: hotkeys desactivados."""
    return _circle((127, 140, 141, 255))


def loading() -> Image.Image:
    """Azul claro: esperando respuesta de la API."""
    return _circle((135, 206, 250, 255))


def ready() -> Image.Image:
    """Verde oscuro con check: respuesta lista para pegar."""
    img = _circle((25, 111, 61, 255))
    draw = ImageDraw.Draw(img)
    draw.line([(20, 33), (29, 43), (45, 22)], fill=(255, 255, 255, 255), width=6)
    return img


def error() -> Image.Image:
    """Rojo con cruz: hubo un error con Claude."""
    img = _circle((231, 76, 60, 255))
    draw = ImageDraw.Draw(img)
    draw.line([(23, 23), (41, 41)], fill=(255, 255, 255, 255), width=6)
    draw.line([(41, 23), (23, 41)], fill=(255, 255, 255, 255), width=6)
    return img
