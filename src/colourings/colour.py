from __future__ import annotations

import hashlib
import math
import warnings
from collections.abc import Callable, Generator, Sequence
from typing import Any, Protocol

from .conversions import (
    cmyk2hsl,
    hex2hsl,
    hex2rgb,
    hex2web,
    hsl2cmyk,
    hsl2hsla,
    hsl2hslaf,
    hsl2hslf,
    hsl2hsv,
    hsl2lab,
    hsl2lch,
    hsl2oklab,
    hsl2oklch,
    hsl2rgb,
    hsl2rgbf,
    hsl2xyz,
    hsl2yuv,
    hsla2hsl,
    hslf2hsl,
    hsv2hsl,
    lab2hsl,
    lch2hsl,
    oklab2hsl,
    oklch2hsl,
    rgb2hex,
    rgb2hsl,
    rgb2rgba,
    rgb2rgbaf,
    rgba2hsl,
    rgbaf2hsl,
    rgbf2hsl,
    web2hex,
    web2hsl,
    xyz2hsl,
    yuv2hsl,
)
from .definitions import CMYK as CMYKTuple

## The colour tuple types are aliased because this module already exposes
## ``HSL`` and ``RGB`` as the named-colour accessor singletons defined below.
from .definitions import COLOR_NAME_TO_RGB, linspace
from .definitions import HSL as HSLTuple
from .definitions import HSLA as HSLATuple
from .definitions import HSV as HSVTuple
from .definitions import LAB as LABTuple
from .definitions import LCH as LCHTuple
from .definitions import OKLAB as OKLABTuple
from .definitions import OKLCH as OKLCHTuple
from .definitions import RGB as RGBTuple
from .definitions import RGBA as RGBATuple
from .definitions import XYZ as XYZTuple
from .definitions import YUV as YUVTuple
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


## Interpolation spaces for ``color_scale``. The key is the ``Color`` property
## that reads the space, and the value pairs the conversion that takes an
## interpolated triple back to HSL with the index of the space's hue channel,
## or ``None`` when the space is rectangular and has no hue to take an arc
## around.
_SCALE_SPACES: dict[str, tuple[Callable[[Sequence[float]], HSLTuple], int | None]] = {
    "hsl": (lambda values: HSLTuple(*values), 0),
    "lab": (lab2hsl, None),
    "lch": (lch2hsl, 2),
    "oklab": (oklab2hsl, None),
    "oklch": (oklch2hsl, 2),
}


def _unwrap_hue(start: list[float], end: list[float], index: int, longer: bool) -> None:
    """Shift one endpoint's hue in place so interpolation takes the wanted arc.

    The hue is rewritten as a fraction of a turn rather than left in degrees,
    so that the arithmetic here -- and so the scale it produces -- is unchanged
    from when ``color_scale`` only handled HSL.

    Parameters
    ----------
    start : list[float]
        Components of the colour the section starts on.
    end : list[float]
        Components of the colour the section ends on.
    index : int
        Position of the hue channel within those components.
    longer : bool
        Whether to take the longer arc around the hue circle.

    Returns
    -------
    None
        Both lists are modified in place.
    """
    h1 = start[index] / 360.0
    h2 = end[index] / 360.0
    if longer == (abs(h1 - h2) < 0.5):
        if h1 < h2:
            h1 += 1
        else:
            h2 += 1
    start[index], end[index] = h1, h2


def color_scale(
    colors: Sequence[Color | Colour],
    num_steps: int,
    longer: bool = False,
    space: str = "hsl",
) -> list[Color]:
    """Create a color scale by linearly interpolating in a chosen space.

    HSL stays the default, because changing it would change the output of
    every existing caller, but it is the weakest of the five for a gradient.
    Its lightness is a geometric construction rather than a perceptual one, so
    an HSL ramp is unevenly spaced to the eye and its brightness need not even
    be monotonic: blue to yellow in nine steps rises, dips, and rises again.
    Being polar, it also swings through hues that are in neither endpoint --
    that same ramp runs through magenta and red.

    ``oklab`` is the one to reach for. It is perceptually uniform, so steps are
    evenly spaced, and rectangular, so there is no hue arc to sweep or to
    choose. Use ``oklch`` when that sweep is the point. ``lab`` and ``lch`` are
    the CIE equivalents, and are less uniform than the Ok pair, most visibly
    around blue.

    Parameters
    ----------
    colors : Sequence[Color | Colour]
        Ordered color sequence used as interpolation control points.
    num_steps : int
        Total number of colors to generate, including endpoints.
    longer : bool, default=False
        Whether to take the longer hue arc instead of the shortest arc. Only
        meaningful in a space that has a hue channel.
    space : str, default="hsl"
        Space to interpolate in: ``"hsl"``, ``"lab"``, ``"lch"``, ``"oklab"``
        or ``"oklch"``.

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
    ValueError
        Raised when ``space`` is not one of the supported spaces.
    ValueError
        Raised when ``longer`` is requested in a space without a hue channel.
    """
    # checks
    if len(colors) < 2:
        raise ValueError("At least two colours are required to make a scale.")
    if len(colors) > num_steps:
        raise ValueError(
            "Number of steps must be greater than or equal to the number of colors."
        )
    if space not in _SCALE_SPACES:
        raise ValueError(
            f"Unknown interpolation space {space!r}. Choose one of: "
            f"{', '.join(sorted(_SCALE_SPACES))}."
        )
    to_hsl, hue_index = _SCALE_SPACES[space]
    if longer and hue_index is None:
        raise ValueError(
            f"The longer hue arc is not defined in {space!r}, which has no hue channel."
        )

    # linearly interpolate between colours
    num_sections = len(colors) - 1
    num_steps_per_iter = math.floor((num_steps - len(colors)) / num_sections)
    remainder = ((num_steps - len(colors)) / num_sections) % 1
    out = []
    added = 0
    for i in range(num_sections):
        # colour definitions
        start = list(getattr(colors[i], space))
        end = list(getattr(colors[i + 1], space))
        if hue_index is not None:
            _unwrap_hue(start, end, hue_index, longer)

        # number of colours
        num_colors = num_steps_per_iter + 2  # add 2 for start and end colours
        if round(remainder * (i + 1) - added, 7) >= 1:
            num_colors += 1
            added += 1

        # interpolate
        channels = [linspace(a, b, num_colors) for a, b in zip(start, end, strict=True)]
        if hue_index is not None:
            channels[hue_index] = [(v * 360) % 360 for v in channels[hue_index]]
        add = [Color(hsl=to_hsl(values)) for values in zip(*channels, strict=True)]

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
        HSV components as ``(h, s, v)`` with hue in ``[0, 360]`` and
        saturation/value in ``[0, 100]``.
    xyz : Sequence[int | float] | None, optional
        CIE XYZ components under D65, scaled so that white has ``y`` of 100.
    lab : Sequence[int | float] | None, optional
        CIE L*a*b* components with lightness in ``[0, 100]``.
    lch : Sequence[int | float] | None, optional
        Cylindrical CIE LCh components with hue in ``[0, 360]``.
    oklab : Sequence[int | float] | None, optional
        Oklab components with lightness in ``[0, 1]`` and a/b in
        ``[-0.4, 0.4]``.
    oklch : Sequence[int | float] | None, optional
        Cylindrical Oklab components with chroma in ``[0, 0.4]`` and hue in
        ``[0, 360]``.
    cmyk : Sequence[int | float] | None, optional
        CMYK components, each in ``[0, 100]``.
    yuv : Sequence[int | float] | None, optional
        BT.601 YUV components with luma in ``[0, 1]``.
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
        xyz: Sequence[int | float] | None = None,
        lab: Sequence[int | float] | None = None,
        lch: Sequence[int | float] | None = None,
        oklab: Sequence[int | float] | None = None,
        oklch: Sequence[int | float] | None = None,
        cmyk: Sequence[int | float] | None = None,
        yuv: Sequence[int | float] | None = None,
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
                    xyz,
                    lab,
                    lch,
                    oklab,
                    oklch,
                    cmyk,
                    yuv,
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
                "Only one of 'color', 'web', 'hsl', 'hsla', 'hslf', 'hslaf', 'hsv', 'xyz', 'lab', 'lch', 'oklab', 'oklch', 'cmyk', 'yuv', 'hex', 'hex_l', 'rgb', 'rgba', 'rgbf', 'rgbaf' or 'pick_for' may be entered."
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
        elif hsv is not None:
            self.hsl = hsv2hsl(hsv)
        elif xyz is not None:
            self.hsl = xyz2hsl(xyz)
        elif lab is not None:
            self.hsl = lab2hsl(lab)
        elif lch is not None:
            self.hsl = lch2hsl(lch)
        elif oklab is not None:
            self.hsl = oklab2hsl(oklab)
        elif oklch is not None:
            self.hsl = oklch2hsl(oklch)
        elif cmyk is not None:
            self.hsl = cmyk2hsl(cmyk)
        elif yuv is not None:
            self.hsl = yuv2hsl(yuv)
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
        else:  # pragma: no cover
            ## Unreachable: the check above proves exactly one input is set and
            ## every one of them has a branch. Kept so that adding a new input
            ## without a branch fails loudly instead of leaving _hsl unset.
            raise UnknownColorError("Input not recognised")

        # set attributes
        self.equality = equality
        self.alpha = alpha if alpha is not None else 1.0
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_hsl(self) -> HSLTuple:
        return self._hsl

    def get_hsv(self) -> HSVTuple:
        return hsl2hsv(self._hsl)

    def get_xyz(self) -> XYZTuple:
        return hsl2xyz(self._hsl)

    def get_lab(self) -> LABTuple:
        return hsl2lab(self._hsl)

    def get_lch(self) -> LCHTuple:
        return hsl2lch(self._hsl)

    def get_oklab(self) -> OKLABTuple:
        return hsl2oklab(self._hsl)

    def get_oklch(self) -> OKLCHTuple:
        return hsl2oklch(self._hsl)

    def get_cmyk(self) -> CMYKTuple:
        return hsl2cmyk(self._hsl)

    def get_yuv(self) -> YUVTuple:
        return hsl2yuv(self._hsl)

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

    def set_hsv(self, value: Sequence[float]) -> None:
        self.hsl = hsv2hsl(value)

    def set_xyz(self, value: Sequence[float]) -> None:
        self.hsl = xyz2hsl(value)

    def set_lab(self, value: Sequence[float]) -> None:
        self.hsl = lab2hsl(value)

    def set_lch(self, value: Sequence[float]) -> None:
        self.hsl = lch2hsl(value)

    def set_oklab(self, value: Sequence[float]) -> None:
        self.hsl = oklab2hsl(value)

    def set_oklch(self, value: Sequence[float]) -> None:
        self.hsl = oklch2hsl(value)

    def set_cmyk(self, value: Sequence[float]) -> None:
        self.hsl = cmyk2hsl(value)

    def set_yuv(self, value: Sequence[float]) -> None:
        self.hsl = yuv2hsl(value)

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
    hsv = property(get_hsv, set_hsv)
    xyz = property(get_xyz, set_xyz)
    lab = property(get_lab, set_lab)
    lch = property(get_lch, set_lch)
    oklab = property(get_oklab, set_oklab)
    oklch = property(get_oklch, set_oklch)
    cmyk = property(get_cmyk, set_cmyk)
    yuv = property(get_yuv, set_yuv)
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
        space: str = "hsl",
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
        space : str, default="hsl"
            Space to interpolate in, as described on :func:`color_scale`.

        Returns
        -------
        Generator[Color, None, None]
            Generator yielding interpolated colors.
        """
        yield from color_scale((self, Color(value)), steps, longer=longer, space=space)

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
