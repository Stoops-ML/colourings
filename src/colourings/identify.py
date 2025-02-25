from collections.abc import Sequence
from typing import Any

from .definitions import COLOR_NAME_TO_RGB, LONG_HEX_COLOR, SHORT_HEX_COLOR


def is_long_hex(color: str) -> bool:
    return bool(LONG_HEX_COLOR.fullmatch(color))


def is_short_hex(color: str) -> bool:
    return bool(SHORT_HEX_COLOR.fullmatch(color))


def is_rgb(color: Any) -> bool:
    if not isinstance(color, Sequence):
        return False
    if len(color) != 3:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 255):
            return False
    return True


def is_rgba(color: Any) -> bool:
    if not isinstance(color, Sequence):
        return False
    if len(color) != 4:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 1):
            return False
    return True


def is_web(color: str) -> bool:
    return color in COLOR_NAME_TO_RGB or is_long_hex(color) or is_short_hex(color)


def is_hsl(color: Any) -> bool:
    if not isinstance(color, Sequence):
        return False
    if len(color) != 3:
        return False
    if isinstance(color[0], int | float) and not 0 <= color[0] <= 360:
        return False
    for channel in color[1:]:
        if not isinstance(channel, int | float) or not (0 <= channel <= 1):
            return False
    return True


def is_hsla(color: Any) -> bool:
    if not isinstance(color, Sequence):
        return False
    if len(color) != 4:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 1):
            return False
    return True
