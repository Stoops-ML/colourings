from __future__ import annotations

import hashlib
import math
import tkinter
import warnings
from collections.abc import Callable, Iterable
from typing import Any

from .conversions import (
    hex2hsl,
    hex2rgb,
    hex2web,
    hsl2hsla,
    hsl2rgb,
    hsla2hsl,
    rgb2hex,
    rgb2hsl,
    rgb2rgba,
    rgba2hsl,
    web2hex,
    web2hsl,
)
from .definitions import COLOR_NAME_TO_RGB
from .identify import (
    is_hsl,
    is_hsla,
    is_long_hex,
    is_rgb,
    is_rgba,
    is_short_hex,
    is_web,
)


class C_HSL:
    def __getattr__(self, value):
        label = value.lower()
        if label in COLOR_NAME_TO_RGB:
            return rgb2hsl(COLOR_NAME_TO_RGB[label])
        raise AttributeError(f"{self.__class__} instance has no attribute {value}")


HSL = C_HSL()


class C_RGB:
    """RGB colors container. Provides a quick color access."""

    def __getattr__(self, value):
        return hsl2rgb(getattr(HSL, value))


class C_HEX:
    """RGB colors container. Provides a quick color access."""

    def __getattr__(self, value):
        return rgb2hex(getattr(RGB, value))


RGB = C_RGB()
HEX = C_HEX()


def color_scale(begin_hsl, end_hsl, nb, longer=False):
    """Returns a list of nb color HSL tuples between begin_hsl and end_hsl"""
    if nb < 0:
        raise ValueError("Number of colours must be greater than or equal to 0")

    h1, s1, l1 = begin_hsl
    h2, s2, l2 = end_hsl
    h1 /= 360.0
    h2 /= 360.0
    if longer == (abs(h1 - h2) < 0.5):
        if h1 < h2:
            h1 += 1
        else:
            h2 += 1
    return [
        (
            (h1 * 360.0 * (1 - v) + h2 * 360.0 * v) % 360.0,
            s1 * (1 - v) + s2 * v,
            l1 * (1 - v) + l2 * v,
        )
        for v in (float(step) / (nb) for step in range(nb + 1))
    ]


def hash_or_str(obj) -> str:
    try:
        return hash((type(obj).__name__, obj))
    except TypeError:
        ## Adds the type name to make sure two object of different type but
        ## identical string representation get distinguished.
        return type(obj).__name__ + str(obj)


def RGB_color_picker(obj) -> Color:
    """Build a color representation from the string representation of an object.

    This allows to quickly get a color from some data, with the
    additional benefit that the color will be the same as long as the
    (string representation of the) data is the same.
    """

    ## Turn the input into a by 3-dividable string. SHA-384 is good because it
    ## divides into 3 components of the same size, which will be used to
    ## represent the RGB values of the color.
    digest = hashlib.sha384(str(obj).encode("utf-8")).hexdigest()

    ## Split the digest into 3 sub-strings of equivalent size.
    subsize = int(len(digest) / 3)
    splitted_digest = [digest[i * subsize : (i + 1) * subsize] for i in range(3)]

    ## Convert those hexadecimal sub-strings into integer and scale them down
    ## to the 0..1 range.
    max_value = float(int("f" * subsize, 16))
    components = [
        int(d, 16)  ## Make a number from a list with hex digits
        / max_value  ## Scale it down to [0.0, 1.0]
        for d in splitted_digest
    ]

    return Color(rgb2hex(components))  ## Profit!


def RGB_equivalence(c1: Color, c2: Color) -> bool:
    return c1.hex_l == c2.hex_l


def HSL_equivalence(c1: Color, c2: Color) -> bool:
    return c1._hsl == c2._hsl


def identify_color(
    color: str | Iterable[int | float] | Color | Colour,
) -> Callable[[Any], Any]:
    if isinstance(color, Color | Colour):
        return lambda x: x.hsl
    elif (
        isinstance(color, str)
        and is_long_hex(color)
        or isinstance(color, str)
        and is_short_hex(color)
    ):
        return hex2hsl
    elif isinstance(color, str) and is_web(color):
        return web2hsl
    elif isinstance(color, Iterable) and is_rgb(color) and is_hsl(color):
        raise TypeError("Cannot discern whether color is RGB or HSL")
    elif isinstance(color, Iterable) and is_rgb(color):
        return rgb2hsl
    elif isinstance(color, Iterable) and is_hsl(color):
        return lambda x: x
    elif isinstance(color, Iterable) and is_rgba(color) and is_hsla(color):
        raise TypeError("Cannot discern whether color is RGBA or HSLA")
    # elif isinstance(color, Iterable) and is_rgba(color): NOTE: unreachable
    #     return rgba2hsl
    # elif isinstance(color, Iterable) and is_hsla(color): NOTE: unreachable
    #     return hsla2hsl
    else:
        raise TypeError("Cannot identify color.")


class Color:
    """Abstraction of a color object

    Color object keeps information of a color. It can input/output to different
    format (HSL, RGB, HEX, WEB) and their partial representation.
    """

    _hsl = None  # internal representation

    def __init__(  # noqa: C901
        self,
        color: str | Iterable[int | float] | None = None,
        *,
        web: str | None = None,
        hsl: Iterable[int | float] | None = None,
        hsla: Iterable[int | float] | None = None,
        hex: str | None = None,
        hex_l: str | None = None,
        rgb: Iterable[int | float] | None = None,
        rgba: Iterable[int | float] | None = None,
        alpha: float | None = None,
        pick_for: Any = None,
        picker: Callable[[Any], Color] = RGB_color_picker,
        pick_key: Callable[[Any], str] = hash_or_str,
        equality: Callable[[Color, Color], bool] = RGB_equivalence,
        **kwargs,
    ):
        # checks
        if (
            sum(
                v is not None
                for v in (
                    color,
                    web,
                    hsl,
                    hsla,
                    hex,
                    hex_l,
                    rgb,
                    rgba,
                    pick_for,
                )
            )
            != 1
        ):
            raise ValueError(
                "Only one of 'color', 'web', 'hsl', 'hsla', 'hex', 'hex_l', 'rgb', 'rgba' or 'pick_for' may be entered."
            )

        # convert to hsl
        if color is not None:
            func = identify_color(color)
            self.hsl = func(color)
        elif web is not None:
            self.hsl = web2hsl(web)
        elif hsl is not None:
            self.hsl = hsl
        elif hsla is not None:
            if alpha is not None and alpha != hsla[3]:
                raise ValueError(
                    f"Alpha value defined twice and does not have the same value: alpha={alpha} and alpha of hsla={hsla[3]}"
                )
            self.hsl, alpha = hsla2hsl(hsla), hsla[3]
        elif hex is not None:
            self.hsl = hex2hsl(hex)
        elif hex_l is not None:
            self.hsl = hex2hsl(hex_l)
        elif rgb is not None:
            self.hsl = rgb2hsl(rgb)
        elif rgba is not None:
            if alpha is not None and alpha != rgba[3]:
                raise ValueError(
                    f"Alpha value defined twice and does not have the same value: alpha={alpha} and alpha of rgba={rgba[3]}"
                )
            self.hsl, alpha = rgba2hsl(rgba), rgba[3]
        elif pick_for is not None:
            self.hsl = web2hsl(picker(pick_key(pick_for)).web)
        # elif isinstance(color, Color):
        #     self.web = web2hsl(color.web)
        else:
            raise ValueError("Input not recognised")

        # set attributes
        self.equality = equality
        self.alpha = alpha if alpha is not None else 1.0
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, label: str):
        if label.startswith("get_"):
            raise AttributeError(f"'{label}' not found")
        try:
            return getattr(self, "get_" + label)()
        except AttributeError as e:
            raise AttributeError(f"'{label}' not found") from e

    def __setattr__(self, label, value):
        if label not in ["_alpha", "_hsl", "equality"]:
            fc = getattr(self, "set_" + label)
            fc(value)
        else:
            self.__dict__[label] = value

    def get_hsl(self):
        return tuple(self._hsl)

    def get_hex(self):
        return rgb2hex(self.rgb)

    def get_hex_l(self):
        return rgb2hex(self.rgb, force_long=True)

    def get_rgb(self):
        return hsl2rgb(self.hsl)

    def get_rgba(self):
        return rgb2rgba(hsl2rgb(self.hsl), self._alpha)

    def get_hsla(self):
        return hsl2hsla(self.hsl, self._alpha)

    def get_hue(self):
        return self.hsl[0]

    def get_saturation(self):
        return self.hsl[1]

    def get_lightness(self):
        return self.hsl[2]

    def get_luminance(self):
        r, g, b, _ = self.get_rgba()
        return math.sqrt(0.299 * r**2 + 0.587 * g**2 + 0.114 * b**2)

    def get_red(self):
        return self.rgb[0]

    def get_green(self):
        return self.rgb[1]

    def get_blue(self):
        return self.rgb[2]

    def get_alpha(self):
        return self._alpha

    def get_web(self):
        return hex2web(self.hex)

    def set_hsl(self, value) -> None:
        self._hsl = list(value)

    def set_rgb(self, value) -> None:
        self.hsl = rgb2hsl(value)

    def set_hue(self, value) -> None:
        self._hsl[0] = value

    def set_saturation(self, value) -> None:
        self._hsl[1] = value

    def set_lightness(self, value) -> None:
        self._hsl[2] = value

    def set_red(self, value) -> None:
        _, g, b = self.rgb
        self.rgb = (value, g, b)

    def set_green(self, value) -> None:
        r, _, b = self.rgb
        self.rgb = (r, value, b)

    def set_blue(self, value) -> None:
        r, g, _ = self.rgb
        self.rgb = (r, g, value)

    def set_alpha(self, value) -> None:
        if value < 0 or value > 1:
            raise ValueError("Alpha must be between 0 and 1.")
        self._alpha = value

    def set_hex(self, value) -> None:
        self.rgb = hex2rgb(value)

    def set_hex_l(self, value) -> None:
        self.set_hex(value)

    def set_web(self, value) -> None:
        self.hex = web2hex(value)

    def range_to(self, value, steps, longer=False):
        """range of color generation"""
        for hsl in color_scale(self._hsl, Color(value).hsl, steps - 1, longer=longer):
            yield Color(hsl=hsl)

    def preview(self, size_x=200, size_y=200):
        if not isinstance(size_x, int | float):
            raise TypeError("`size_x` must be of integer or float type")
        if not isinstance(size_y, int | float):
            raise TypeError("`size_y` must be of integer or float type")
        if self._alpha != 1:
            warnings.warn(
                f"Alpha set to {self._alpha}, but is not displayed in the window.",
                stacklevel=2,
            )
        root = tkinter.Tk()
        root.geometry(f"{size_x}x{size_y}")
        root.config(background=self.get_hex_l())
        root.title(f"{str(self)} preview")
        root.mainloop()

    def __str__(self):
        return f"{self.web}"

    def __repr__(self):
        return f"<Color {self.web}>"

    def __eq__(self, other):
        if isinstance(other, Color | Colour):
            return self.equality(self, other)
        raise NotImplementedError("Other object must be of type `Color` or `Colour`")


class Colour(Color): ...


def make_color_factory(**kwargs_defaults):
    def ColorFactory(*args, **kwargs):
        new_kwargs = kwargs_defaults.copy()
        new_kwargs.update(kwargs)
        return Color(*args, **new_kwargs)

    return ColorFactory
