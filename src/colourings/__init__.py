from .colour import Color, Colour, color_scale, colour_scale
from .errors import (
    AmbiguousColorError,
    ColorError,
    InvalidColorError,
    UnknownColorError,
)

__all__ = [
    "AmbiguousColorError",
    "Color",
    "ColorError",
    "Colour",
    "InvalidColorError",
    "UnknownColorError",
    "color_scale",
    "colour_scale",
]

__version__ = "1.0.0"
