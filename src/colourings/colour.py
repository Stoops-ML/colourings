from __future__ import annotations

import hashlib
import math
import warnings
from collections.abc import Callable, Generator, Sequence
from typing import Any, Protocol

from .conversions import (
    hex2hsl,
    hex2rgb,
    hex2web,
    hsl2hsla,
    hsl2hslaf,
    hsl2hslf,
    hsl2rgb,
    hsl2rgbf,
    hsla2hsl,
    hslf2hsl,
    rgb2hex,
    rgb2hsl,
    rgb2rgba,
    rgb2rgbaf,
    rgba2hsl,
    rgbaf2hsl,
    rgbf2hsl,
    web2hex,
    web2hsl,
)

## The colour tuple types are aliased because this module already exposes
## ``HSL`` and ``RGB`` as the named-colour accessor singletons defined below.
from .definitions import COLOR_NAME_TO_RGB, linspace
from .definitions import HSL as HSLTuple
from .definitions import HSLA as HSLATuple
from .definitions import RGB as RGBTuple
from .definitions import RGBA as RGBATuple
from .definitions import HSLAf as HSLAfTuple
from .definitions import HSLf as HSLfTuple
from .definitions import RGBAf as RGBAfTuple
from .definitions import RGBf as RGBfTuple
from .errors import (
    AmbiguousColorError,
    InvalidColorError,
    UnknownColorError,
)
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
    """Container exposing named colors as RGB tuples.

    Returns
    -------
    tuple[float, float, float]
        RGB values for a known color name.
    """

    def __getattr__(self, value):
        return hsl2rgb(getattr(HSL, value))


class C_HEX:
    """Container exposing named colors as hexadecimal strings.

    Returns
    -------
    str
        Hexadecimal color value for a known color name.
    """

    def __getattr__(self, value):
        return rgb2hex(getattr(RGB, value))


RGB = C_RGB()
HEX = C_HEX()


def color_scale(
    colors: Sequence[Color | Colour], num_steps: int, longer: bool = False
) -> list[Color]:
    """Create a color scale by linearly interpolating in HSL space.

    TODO: implement better interpolation technique: https://www.alanzucconi.com/2016/01/06/colour-interpolation/

    Parameters
    ----------
    colors : Sequence[Color | Colour]
        Ordered color sequence used as interpolation control points.
    num_steps : int
        Total number of colors to generate, including endpoints.
    longer : bool, default=False
        Whether to take the longer hue arc instead of the shortest arc.

    Returns
    -------
    list[Color]
        Interpolated color list of length ``num_steps``.

    Raises
    ------
    ValueError
        Raised when fewer than two colors are provided.
    ValueError
        Raised when ``num_steps`` is less than the number of control colors.
    """
    # checks
    if len(colors) < 2:
        raise ValueError("At least two colours are required to make a scale.")
    if len(colors) > num_steps:
        raise ValueError(
            "Number of steps must be greater than or equal to the number of colors."
        )

    # linearly interpolate between colours
    num_sections = len(colors) - 1
    num_steps_per_iter = math.floor((num_steps - len(colors)) / num_sections)
    remainder = ((num_steps - len(colors)) / num_sections) % 1
    out = []
    added = 0
    for i in range(num_sections):
        # colour definitions
        h1, s1, l1 = colors[i].hsl
        h2, s2, l2 = colors[i + 1].hsl
        h1 /= 360.0
        h2 /= 360.0
        if longer == (abs(h1 - h2) < 0.5):
            if h1 < h2:
                h1 += 1
            else:
                h2 += 1

        # number of colours
        num_colors = num_steps_per_iter + 2  # add 2 for start and end colours
        if round(remainder * (i + 1) - added, 7) >= 1:
            num_colors += 1
            added += 1

        # interpolate
        hs = [(v * 360) % 360 for v in linspace(h1, h2, num_colors)]
        ss = linspace(s1, s2, num_colors)
        ls = linspace(l1, l2, num_colors)
        add = [Color(hsl=(_h, _s, _l)) for _h, _s, _l in zip(hs, ss, ls, strict=False)]

        # add to output
        if i == 0:
            out.extend(add)
        else:
            out.extend(add[1:])
    return out


colour_scale = color_scale


class PickKey(Protocol):
    """Callable reducing an arbitrary object to a stable, hashable pick key."""

    def __call__(self, obj: Any, /) -> str | int: ...


class ColorPicker(Protocol):
    """Callable turning a pick key into a deterministic color."""

    def __call__(self, key: Any, /) -> Color: ...


class ColorEquality(Protocol):
    """Callable deciding whether two colors are considered equal."""

    def __call__(self, c1: Color, c2: Color, /) -> bool: ...


def hash_or_str(obj: object) -> str | int:
    """Return a stable hash key for an object, with a string fallback.

    Parameters
    ----------
    obj : object
        Object to key.

    Returns
    -------
    str | int
        Hash-based key when hashable; otherwise a type-qualified string key.
    """
    try:
        return hash((type(obj).__name__, obj))
    except TypeError:
        ## Adds the type name to make sure two object of different type but
        ## identical string representation get distinguished.
        return f"{type(obj).__name__}{obj}"


def RGB_color_picker(obj: object) -> Color:
    """Build a color representation from the string representation of an object.

    This allows to quickly get a color from some data, with the
    additional benefit that the color will be the same as long as the
    (string representation of the) data is the same.

    Parameters
    ----------
    obj : object
        Object used to derive a deterministic color.

    Returns
    -------
    Color
        Color generated from the SHA-384 digest of the object string.
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
    """Compare two colors by long hexadecimal RGB equivalence.

    Parameters
    ----------
    c1 : Color
        First color.
    c2 : Color
        Second color.

    Returns
    -------
    bool
        ``True`` when both colors have the same ``hex_l`` value.
    """
    return c1.hex_l == c2.hex_l


def HSL_equivalence(c1: Color, c2: Color) -> bool:
    """Compare two colors by internal HSL tuple equivalence.

    Parameters
    ----------
    c1 : Color
        First color.
    c2 : Color
        Second color.

    Returns
    -------
    bool
        ``True`` when both colors have identical internal HSL values.
    """
    return c1._hsl == c2._hsl


def identify_color(
    color: str | Sequence[int | float] | Color | Colour,
) -> Callable[[Any], HSLTuple]:
    """Identify a color input format and return its HSL conversion callable.

    Parameters
    ----------
    color : str | Sequence[int | float] | Color | Colour
        Candidate color value in one supported representation.

    Returns
    -------
    Callable[[Any], HSLTuple]
        Converter function that maps the provided representation to HSL.

    Raises
    ------
    AmbiguousColorError
        Raised when the value is ambiguous between RGB/HSL or RGBA/HSLA.
    UnknownColorError
        Raised when the format cannot be identified.
    """
    # checks
    if (
        isinstance(color, Sequence)
        and len(color) == 3
        and is_rgb(color)
        and is_hsl(color)
    ):
        raise AmbiguousColorError("Cannot determine whether color is RGB or HSL.")
    elif (
        isinstance(color, Sequence)
        and len(color) == 4
        and is_rgba(color)
        and is_hsla(color)
    ):
        raise AmbiguousColorError("Cannot determine whether color is RGBA or HSLA.")
    else:
        pass

    # identify colour
    if isinstance(color, Color | Colour):
        return lambda x: HSLTuple(*x.hsl)
    elif (
        isinstance(color, str)
        and is_long_hex(color)
        or isinstance(color, str)
        and is_short_hex(color)
    ):
        return hex2hsl
    elif isinstance(color, str) and is_web(color):
        return web2hsl
    elif isinstance(color, Sequence) and is_rgb(color):
        return rgb2hsl
    elif isinstance(color, Sequence) and is_hsl(color):
        return lambda x: HSLTuple(*x)
    # elif isinstance(color, Sequence) and is_rgba(color): NOTE: unreachable
    #     return rgba2hsl
    # elif isinstance(color, Sequence) and is_hsla(color): NOTE: unreachable
    #     return hsla2hsl
    else:
        raise UnknownColorError("Cannot identify color.")


class Color:
    """Abstraction over a color with multi-format conversion properties.

    Parameters
    ----------
    color : str | Sequence[int | float] | Color | None, optional
        Generic color input in any supported format.
    web : str | None, optional
        Web color name or hex string.
    hsl : Sequence[int | float] | None, optional
        HSL components as ``(h, s, l)``.
    hsla : Sequence[int | float] | None, optional
        HSLA components as ``(h, s, l, a)`` with alpha in percent.
    hslf : Sequence[int | float] | None, optional
        Normalized HSL components in ``[0, 1]``.
    hslaf : Sequence[int | float] | None, optional
        Normalized HSLA components in ``[0, 1]``.
    hsv : Sequence[int | float] | None, optional
        Reserved parameter for HSV input.
    hex : str | None, optional
        Hexadecimal color string.
    hex_l : str | None, optional
        Long hexadecimal color string.
    rgb : Sequence[int | float] | None, optional
        RGB components in ``[0, 255]``.
    rgba : Sequence[int | float] | None, optional
        RGBA components with alpha in ``[0, 255]``.
    rgbf : Sequence[int | float] | None, optional
        Normalized RGB components in ``[0, 1]``.
    rgbaf : Sequence[int | float] | None, optional
        Normalized RGBA components in ``[0, 1]``.
    alpha : float | None, optional
        Explicit alpha value in ``[0, 1]``.
    pick_for : object, optional
        Arbitrary value used to deterministically pick a color.
    picker : ColorPicker, default=RGB_color_picker
        Picker function used with ``pick_for``.
    pick_key : PickKey, default=hash_or_str
        Key function used before passing values to ``picker``.
    equality : ColorEquality, default=RGB_equivalence
        Equality strategy used by ``__eq__``.
    **kwargs : Any
        Additional attributes attached to the instance.

    Raises
    ------
    ValueError
        Raised when none or more than one primary color input is provided.
    ValueError
        Raised when alpha is provided inconsistently across inputs.
    UnknownColorError
        Raised when the input does not match any supported color format.
    """

    ## Only these three are stored; every colour format below is a property
    ## computed from them. Declaring them as slots keeps a mistyped attribute an
    ## AttributeError instead of silently becoming a new attribute.
    __slots__ = ("_alpha", "_hsl", "equality")

    _hsl: HSLTuple  # internal representation
    _alpha: float
    equality: ColorEquality

    def __init__(  # noqa: C901
        self,
        color: str | Sequence[int | float] | Color | None = None,
        *,
        web: str | None = None,
        hsl: Sequence[int | float] | None = None,
        hsla: Sequence[int | float] | None = None,
        hslf: Sequence[int | float] | None = None,
        hslaf: Sequence[int | float] | None = None,
        hsv: Sequence[int | float] | None = None,
        hex: str | None = None,
        hex_l: str | None = None,
        rgb: Sequence[int | float] | None = None,
        rgba: Sequence[int | float] | None = None,
        rgbf: Sequence[int | float] | None = None,
        rgbaf: Sequence[int | float] | None = None,
        alpha: float | None = None,
        pick_for: object = None,
        picker: ColorPicker = RGB_color_picker,
        pick_key: PickKey = hash_or_str,
        equality: ColorEquality = RGB_equivalence,
        **kwargs: Any,
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
                    hslf,
                    hslaf,
                    hsv,
                    hex,
                    hex_l,
                    rgb,
                    rgba,
                    rgbf,
                    rgbaf,
                    pick_for,
                )
            )
            != 1
        ):
            raise ValueError(
                "Only one of 'color', 'web', 'hsl', 'hsla', 'hslf', 'hslaf', 'hex', 'hex_l', 'rgb', 'rgba', 'rgbf', 'rgbaf' or 'pick_for' may be entered."
            )

        # convert to hsl
        if color is not None:
            if isinstance(color, str):
                color = color.lower()
            func = identify_color(color)
            self.hsl = func(color)
        elif web is not None:
            web = web.lower()
            self.hsl = web2hsl(web)
        elif hsl is not None:
            self.hsl = hsl
        elif hsla is not None:
            if alpha is not None and alpha != hsla[3]:
                raise ValueError(
                    f"Alpha value defined twice and does not have the same value: alpha={alpha} and alpha of hsla={hsla[3]}"
                )
            self.hsl, alpha = hsla2hsl(hsla), hsla[3] / 100
        elif hslf is not None:
            self.hsl = hslf2hsl(hslf)
        elif hslaf is not None:
            if alpha is not None and alpha != hslaf[3]:
                raise ValueError(
                    f"Alpha value defined twice and does not have the same value: alpha={alpha} and alpha of hslaf={hslaf[3]}"
                )
            self.hsl, alpha = hslf2hsl(hslaf[:3]), hslaf[3]
        elif hex is not None:
            self.hsl = hex2hsl(hex)
        elif hex_l is not None:
            self.hsl = hex2hsl(hex_l)
        elif rgb is not None:
            self.hsl = rgb2hsl(rgb)
        elif rgba is not None:
            if alpha is not None and alpha != rgba[3] / 255.0:
                raise ValueError(
                    f"Alpha value defined twice and does not have the same value: alpha={alpha} and alpha of rgba={rgba[3] / 255.0}"
                )
            self.hsl, alpha = rgba2hsl(rgba), rgba[3] / 255.0
        elif rgbf is not None:
            self.hsl = rgbf2hsl(rgbf)
        elif rgbaf is not None:
            if alpha is not None and alpha != rgbaf[3]:
                raise ValueError(
                    f"Alpha value defined twice and does not have the same value: alpha={alpha} and alpha of rgbaf={rgbaf[3]}"
                )
            self.hsl, alpha = rgbaf2hsl(rgbaf), rgbaf[3]
        elif pick_for is not None:
            self.hsl = web2hsl(picker(pick_key(pick_for)).web)
        # elif isinstance(color, Color):
        #     self.web = web2hsl(color.web)
        else:
            raise UnknownColorError("Input not recognised")

        # set attributes
        self.equality = equality
        self.alpha = alpha if alpha is not None else 1.0
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_hsl(self) -> HSLTuple:
        return self._hsl

    def get_hslf(self) -> HSLfTuple:
        return hsl2hslf(self._hsl)

    def get_hex(self) -> str:
        return rgb2hex(self.rgb)

    def get_hex_l(self) -> str:
        return rgb2hex(self.rgb, force_long=True)

    def get_rgb(self) -> RGBTuple:
        return hsl2rgb(self.hsl)

    def get_rgbf(self) -> RGBfTuple:
        return hsl2rgbf(self.hsl)

    def get_rgba(self) -> RGBATuple:
        return rgb2rgba(hsl2rgb(self.hsl), self._alpha)

    def get_rgbaf(self) -> RGBAfTuple:
        return rgb2rgbaf(hsl2rgb(self.hsl), self._alpha)

    def get_hsla(self) -> HSLATuple:
        return hsl2hsla(self.hsl, self._alpha)

    def get_hslaf(self) -> HSLAfTuple:
        return hsl2hslaf(self.hsl, self._alpha)

    def get_hue(self) -> float:
        return self.hsl.hue

    def get_saturation(self) -> float:
        return self.hsl.saturation

    def get_lightness(self) -> float:
        return self.hsl.lightness

    def get_luminance(self) -> float:
        r, g, b = self.get_rgbf()
        return math.sqrt(0.299 * r**2 + 0.587 * g**2 + 0.114 * b**2)

    def get_red(self) -> float:
        return self.rgb.red

    def get_green(self) -> float:
        return self.rgb.green

    def get_blue(self) -> float:
        return self.rgb.blue

    def get_alpha(self) -> float:
        return self._alpha

    def get_web(self) -> str:
        return hex2web(self.hex)

    def set_hsl(self, value: Sequence[float]) -> None:
        if not is_hsl(value):
            raise InvalidColorError("Value is not a valid HSL")
        ## Stored as float so that every colour attribute reports floats,
        ## whatever numeric type the caller supplied.
        self._hsl = HSLTuple(float(value[0]), float(value[1]), float(value[2]))

    def set_rgb(self, value: Sequence[float]) -> None:
        self.hsl = rgb2hsl(value)

    def set_rgbf(self, value: Sequence[float]) -> None:
        self.hsl = rgbf2hsl(value)

    def set_rgba(self, value: Sequence[float]) -> None:
        self.hsl = rgba2hsl(value)

    def set_rgbaf(self, value: Sequence[float]) -> None:
        self.hsl = rgbaf2hsl(value)

    def set_hue(self, value: float) -> None:
        self.hsl = HSLTuple(value, self.hsl.saturation, self.hsl.lightness)

    def set_saturation(self, value: float) -> None:
        self.hsl = HSLTuple(self.hsl.hue, value, self.hsl.lightness)

    def set_lightness(self, value: float) -> None:
        self.hsl = HSLTuple(self.hsl.hue, self.hsl.saturation, value)

    def set_red(self, value: float) -> None:
        self.rgb = RGBTuple(value, self.rgb.green, self.rgb.blue)

    def set_green(self, value: float) -> None:
        self.rgb = RGBTuple(self.rgb.red, value, self.rgb.blue)

    def set_blue(self, value: float) -> None:
        self.rgb = RGBTuple(self.rgb.red, self.rgb.green, value)

    def set_alpha(self, value: float) -> None:
        if not 0 <= value <= 1:
            raise InvalidColorError("Alpha must be between 0 and 1.")
        self._alpha = float(value)

    def set_hex(self, value: str) -> None:
        self.rgb = hex2rgb(value)

    def set_hex_l(self, value: str) -> None:
        self.set_hex(value)

    def set_web(self, value: str) -> None:
        self.hex = web2hex(value)

    ## The colour formats are properties over the accessors above, so they are
    ## visible to type checkers, editors and dir(), and reading one is a plain
    ## descriptor call. Those without a ``set_*`` accessor are read-only.
    hsl = property(get_hsl, set_hsl)
    rgb = property(get_rgb, set_rgb)
    rgbf = property(get_rgbf, set_rgbf)
    rgba = property(get_rgba, set_rgba)
    rgbaf = property(get_rgbaf, set_rgbaf)
    hex = property(get_hex, set_hex)
    hex_l = property(get_hex_l, set_hex_l)
    web = property(get_web, set_web)
    hue = property(get_hue, set_hue)
    saturation = property(get_saturation, set_saturation)
    lightness = property(get_lightness, set_lightness)
    red = property(get_red, set_red)
    green = property(get_green, set_green)
    blue = property(get_blue, set_blue)
    alpha = property(get_alpha, set_alpha)

    hslf = property(get_hslf)
    hsla = property(get_hsla)
    hslaf = property(get_hslaf)
    luminance = property(get_luminance)

    def range_to(
        self,
        value: str | Sequence[int | float] | Color,
        steps: int,
        longer: bool = False,
    ) -> Generator[Color, None, None]:
        """Generate a color range from this color to another color.

        Parameters
        ----------
        value : str | Sequence[int | float] | Color
            Target color in any supported input format.
        steps : int
            Number of colors to generate including both endpoints.
        longer : bool, default=False
            Whether to interpolate along the longer hue path.

        Returns
        -------
        Generator[Color, None, None]
            Generator yielding interpolated colors.
        """
        yield from color_scale((self, Color(value)), steps, longer=longer)

    def preview(self, size_x: int | float = 200, size_y: int | float = 200) -> None:
        """Display a Tkinter preview window filled with the current color.

        Parameters
        ----------
        size_x : int | float, default=200
            Window width in pixels.
        size_y : int | float, default=200
            Window height in pixels.

        Returns
        -------
        None
            This method displays a GUI window and does not return a value.
        """
        import tkinter

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

    def __str__(self) -> str:
        return f"{self.web}"

    def __repr__(self) -> str:
        return f"<Color {self.web}>"

    def __eq__(self, other: object) -> bool:
        """Compare two colors using their equality strategies.

        Both operands are consulted, because the strategy is per-instance and
        consulting only ``self`` made ``==`` asymmetric: ``a == b`` and
        ``b == a`` could disagree when the two carried different strategies.
        When they share one, which is the usual case, the result is unchanged.

        Parameters
        ----------
        other : object
            Value to compare against.

        Returns
        -------
        bool
            ``True`` when either color's strategy considers the two equal.
            ``NotImplemented`` for a non-color, so Python falls back to
            identity rather than raising.
        """
        if not isinstance(other, Color):
            return NotImplemented
        return self.equality(self, other) or other.equality(self, other)

    def __hash__(self) -> int:
        """Hash the color by its long hexadecimal form.

        This matches both built-in equality strategies: ``RGB_equivalence``
        compares ``hex_l`` directly, and two colors with equal HSL always
        render the same ``hex_l``. A custom ``equality`` that treats colors
        with different ``hex_l`` as equal breaks that correspondence, and such
        colors should not be relied on as dict keys or set members.

        ``Color`` is mutable, so the hash follows the current value. Do not
        mutate a color while it is held in a set or used as a dict key.

        Returns
        -------
        int
            Hash of the color's ``hex_l`` value.
        """
        return hash(self.hex_l)


class Colour(Color):
    """British-spelling alias of :class:`Color`."""

    __slots__ = ()


def make_color_factory(**kwargs_defaults: Any) -> Callable[..., Color]:
    """Create a factory that instantiates Color with default keyword arguments.

    Parameters
    ----------
    **kwargs_defaults : Any
        Default keyword arguments merged into each factory call.

    Returns
    -------
    Callable[..., Color]
        Callable that creates ``Color`` instances with merged defaults.
    """

    def ColorFactory(*args: Any, **kwargs: Any) -> Color:
        new_kwargs = kwargs_defaults.copy()
        new_kwargs.update(kwargs)
        return Color(*args, **new_kwargs)

    return ColorFactory
