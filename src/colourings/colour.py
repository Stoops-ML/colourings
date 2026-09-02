from __future__ import annotations

import hashlib
import math
import warnings
from collections.abc import Callable, Generator, Sequence
from typing import Any, Protocol

from .conversions import (
    _linear_to_srgb,
    _srgb_to_linear,
    cmyk2hsl,
    contrast_ratio as _contrast_ratio,
    hex2hsl,
    hex2rgb,
    hex2rgba,
    hex2web,
    hexa2hsl,
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
    rgb2grayscale,
    rgb2hex,
    rgb2hsl,
    rgb2relative_luminance,
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
from .css import css2hsl, css2hsla, hsla2css, is_css

## The colour tuple types keep the ``*Tuple`` names, uniformly, so that nothing
## in this module is called ``HSL`` or ``RGB`` -- the names the accessors below
## used to take, and which a caller reaching for the old spelling would
## otherwise receive silently as a NamedTuple.
from .definitions import (
    CMYK as CMYKTuple,
    COLOR_NAME_TO_RGB,
    HSL as HSLTuple,
    HSLA as HSLATuple,
    HSV as HSVTuple,
    LAB as LABTuple,
    LCH as LCHTuple,
    OKLAB as OKLABTuple,
    OKLCH as OKLCHTuple,
    RGB as RGBTuple,
    RGBA as RGBATuple,
    WCAG_CONTRAST_MINIMUMS,
    WCAG_LIGHT_DARK_CROSSOVER,
    XYZ as XYZTuple,
    YUV as YUVTuple,
    HSLAf as HSLAfTuple,
    HSLf as HSLfTuple,
    RGBAf as RGBAfTuple,
    RGBf as RGBfTuple,
    linspace,
)
from .difference import hsl_difference, nearest_named_hsl
from .errors import (
    AmbiguousColorError,
    InvalidColorError,
    UnknownColorError,
)
from .identify import (
    is_hex_alpha,
    is_hsl,
    is_hsla,
    is_long_hex,
    is_rgb,
    is_rgba,
    is_short_hex,
    is_web,
)


def _no_such_colour(container: object, name: str) -> AttributeError:
    """Build the error an accessor raises for a name that is not a colour.

    Takes the container so that each accessor names itself. They used to share
    ``C_HSL``'s error, because the other two look their colours up through it,
    so a typo on ``NAMED_RGB`` reported ``C_HSL`` as the culprit.

    Parameters
    ----------
    container : object
        The accessor the lookup was made on.
    name : str
        The name that was not found.

    Returns
    -------
    AttributeError
        The error to raise.
    """
    return AttributeError(
        f"{type(container).__name__!r} object has no attribute {name!r}"
    )


class C_HSL:
    """Container exposing named colors as HSL tuples."""

    def __getattr__(self, value: str) -> HSLTuple:
        """Look up a named color.

        Parameters
        ----------
        value : str
            A color name, in any case.

        Returns
        -------
        HSLTuple
            HSL values for that name.

        Raises
        ------
        AttributeError
            Raised when the name is not a known color.
        """
        label = value.lower()
        if label in COLOR_NAME_TO_RGB:
            return rgb2hsl(COLOR_NAME_TO_RGB[label])
        raise _no_such_colour(self, value)


NAMED_HSL = C_HSL()


class C_RGB:
    """Container exposing named colors as RGB tuples."""

    def __getattr__(self, value: str) -> RGBTuple:
        """Look up a named color.

        Parameters
        ----------
        value : str
            A color name, in any case.

        Returns
        -------
        RGBTuple
            RGB values for that name.

        Raises
        ------
        AttributeError
            Raised when the name is not a known color.
        """
        try:
            return hsl2rgb(getattr(NAMED_HSL, value))
        except AttributeError:
            raise _no_such_colour(self, value) from None


class C_HEX:
    """Container exposing named colors as hexadecimal strings."""

    def __getattr__(self, value: str) -> str:
        """Look up a named color.

        Parameters
        ----------
        value : str
            A color name, in any case.

        Returns
        -------
        str
            Hexadecimal color value for that name.

        Raises
        ------
        AttributeError
            Raised when the name is not a known color.
        """
        try:
            return rgb2hex(getattr(NAMED_RGB, value))
        except AttributeError:
            raise _no_such_colour(self, value) from None


NAMED_RGB = C_RGB()
NAMED_HEX = C_HEX()


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


def _check_amount(amount: float) -> None:
    """Reject a step or blend position outside ``[0, 1]``.

    Parameters
    ----------
    amount : float
        Value to check.

    Returns
    -------
    None
        Returns nothing when the value is in range.

    Raises
    ------
    ValueError
        Raised when ``amount`` is outside ``[0, 1]``.
    """
    if not 0.0 <= amount <= 1.0:
        raise ValueError(f"`amount` must be between 0 and 1, not {amount!r}.")


def _scale_space(
    space: str, longer: bool
) -> tuple[Callable[[Sequence[float]], HSLTuple], int | None]:
    """Look up an interpolation space, rejecting one that cannot do the job.

    Shared by :func:`color_scale` and :meth:`Color.mix`, so the two accept the
    same spaces and refuse them for the same reasons.

    Parameters
    ----------
    space : str
        Name of the space to interpolate in.
    longer : bool
        Whether the caller asked for the longer hue arc, which only a space
        with a hue channel can give.

    Returns
    -------
    tuple[Callable[[Sequence[float]], HSLTuple], int | None]
        The conversion back to HSL, and the index of the hue channel or
        ``None`` when the space has none.

    Raises
    ------
    ValueError
        Raised when ``space`` is not supported.
    ValueError
        Raised when ``longer`` is asked for in a space without a hue channel.
    """
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
    return to_hsl, hue_index


def color_scale(
    colors: Sequence[Color],
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

    Alpha is interpolated alongside the colour, linearly and independently of
    ``space``, since it is part of no colour space. A scale between opaque
    colours is therefore unchanged, and one between colours of differing
    opacity fades between them rather than coming out opaque throughout.

    Parameters
    ----------
    colors : Sequence[Color]
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
    to_hsl, hue_index = _scale_space(space, longer)

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
        alphas = linspace(colors[i].alpha, colors[i + 1].alpha, num_colors)
        add = [
            Color(hsl=to_hsl(values), alpha=alpha)
            for *values, alpha in zip(*channels, alphas, strict=True)
        ]

        # add to output
        if i == 0:
            out.extend(add)
        else:
            out.extend(add[1:])
    return out


colour_scale = color_scale


def _adjust(
    current: float, amount: float, maximum: float, up: bool, relative: bool
) -> float:
    """Move a channel up or down by an amount given as a fraction of its range.

    The same ``amount`` reads two ways, which is what ``relative`` selects
    between, and both are on a ``[0, 1]`` scale so that the flag changes the
    meaning of the number rather than its units.

    Relative is the default everywhere it is offered because it cannot clip:
    the step is a fraction of the distance still available, so ``1.0`` lands
    exactly on the limit and nothing beyond it is lost. Absolute is a fixed
    step regardless of where the channel already is, which is what Sass's
    ``lighten()`` does and why it is unhelpful near the ends -- lightening an
    already pale colour by a tenth does nothing visible, then clips.

    Parameters
    ----------
    current : float
        Current value of the channel.
    amount : float
        Size of the step, in ``[0, 1]``.
    maximum : float
        Upper bound of the channel; the lower bound is always zero.
    up : bool
        Whether to move towards ``maximum`` rather than towards zero.
    relative : bool
        Whether ``amount`` is a fraction of the remaining distance rather than
        of the whole range.

    Returns
    -------
    float
        The new value, held inside ``[0, maximum]``.
    """
    room = (maximum - current) if up else current
    step = amount * (room if relative else maximum)
    value = current + step if up else current - step
    return min(max(value, 0.0), maximum)


class PickKey(Protocol):
    """Callable reducing an arbitrary object to a stable, hashable pick key."""

    def __call__(self, obj: Any, /) -> str | int: ...


class ColorPicker(Protocol):
    """Callable turning a pick key into a deterministic color."""

    def __call__(self, key: Any, /) -> Color: ...


class ColorEquality(Protocol):
    """Callable deciding whether two colors are considered equal."""

    def __call__(self, c1: Color, c2: Color, /) -> bool: ...


def stable_key(obj: object) -> str:
    """Return a pick key that is the same in every process.

    The type name is included so that two objects of different type with the
    same string form are still told apart.

    Stable for anything whose ``str`` is derived from its value -- strings,
    numbers, tuples, lists, dicts of those. **Not** stable for an object
    relying on the default ``__repr__``, because that contains its address,
    which changes every run and between instances. Give such a class a
    ``__str__``, or pass a ``pick_key`` that reads the fields you care about.

    Parameters
    ----------
    obj : object
        Object to key.

    Returns
    -------
    str
        A type-qualified string key.

    Examples
    --------
    >>> stable_key("user:123")
    'struser:123'
    >>> stable_key([1, 2])
    'list[1, 2]'
    """
    return f"{type(obj).__name__}{obj}"


def hash_or_str(obj: object) -> str | int:
    """Return a hash-based pick key for an object, with a string fallback.

    Was the default ``pick_key``, and is not any more: the key it builds is a
    tuple containing the type name, and hashing a string is salted per
    process, so every hashable object came out a different colour each run
    while every unhashable one -- taking the fallback -- was stable. Which of
    those a caller got depended on nothing they would think to care about.

    Kept for a caller who wants keys that hold within one process and are
    discarded with it, and who would rather compare by ``__eq__`` than by
    string form. :func:`stable_key` is the default now.

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

    ## Built from the normalised components directly. Handing them to rgb2hex
    ## instead treated a [0, 1] value as a [0, 255] one, so every channel
    ## rounded to 0 or 1 and the whole digest collapsed onto eight
    ## near-black colours, which is not enough to tell two objects apart.
    return Color(rgbf=components)  ## Profit!


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


def _alpha_from(given: float | None, carried: float, format_name: str) -> float:
    """Reconcile an ``alpha`` argument with the alpha a color value carries.

    Parameters
    ----------
    given : float | None
        Value passed as the ``alpha`` keyword, if any.
    carried : float
        Alpha carried by the color value, already scaled to ``[0, 1]``.
    format_name : str
        Name of the format the value was identified as, for the error message.

    Returns
    -------
    float
        The alpha to use.

    Raises
    ------
    ValueError
        Raised when both are given and they disagree.
    """
    if given is not None and given != carried:
        raise ValueError(
            f"Alpha value defined twice and does not have the same value: "
            f"alpha={given} and alpha of {format_name}={carried}"
        )
    return carried


## Tried in order: hex before web, since ``is_web`` accepts hex too, and CSS
## last, being the broadest.
_STRING_FORMATS: tuple[tuple[Callable[[str], bool], Callable[[Any], HSLTuple]], ...] = (
    (lambda text: is_long_hex(text) or is_short_hex(text), hex2hsl),
    (is_hex_alpha, hexa2hsl),
    (is_web, web2hsl),
    (is_css, css2hsl),
)

_SEQUENCE_FORMATS: tuple[
    tuple[Callable[[object], bool], Callable[[Any], HSLTuple]], ...
] = (
    (is_rgb, rgb2hsl),
    (is_hsl, lambda values: HSLTuple(*values)),
    (is_rgba, rgba2hsl),
    (is_hsla, hsla2hsl),
)


def identify_color(
    color: str | Sequence[int | float] | Color,
) -> Callable[[Any], HSLTuple]:
    """Identify a color input format and return its HSL conversion callable.

    Parameters
    ----------
    color : str | Sequence[int | float] | Color
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
    if (
        isinstance(color, Sequence)
        and len(color) == 3
        and is_rgb(color)
        and is_hsl(color)
    ):
        raise AmbiguousColorError("Cannot determine whether color is RGB or HSL.")
    if (
        isinstance(color, Sequence)
        and len(color) == 4
        and is_rgba(color)
        and is_hsla(color)
    ):
        raise AmbiguousColorError("Cannot determine whether color is RGBA or HSLA.")

    if isinstance(color, Color):
        return lambda existing: HSLTuple(*existing.hsl)
    if isinstance(color, str):
        for matches, convert in _STRING_FORMATS:
            if matches(color):
                return convert
    elif isinstance(color, Sequence):
        for matches, convert in _SEQUENCE_FORMATS:
            if matches(color):
                return convert
    raise UnknownColorError("Cannot identify color.")


def _apply_property_keywords(color: Color, keywords: dict[str, Any]) -> None:
    """Set writable colour properties named as trailing keyword arguments.

    Parameters
    ----------
    color : Color
        The colour to set them on.
    keywords : dict[str, Any]
        Property names and the values to assign.

    Returns
    -------
    None
        The colour is modified in place.

    Raises
    ------
    ValueError
        Raised when a name is one of the stored attributes.
    AttributeError
        Raised when a name is not a writable property.
    """
    for name, value in keywords.items():
        ## Assigning a slot here would skip the property that validates it,
        ## which is what `__slots__` is present to prevent.
        if name in Color.__slots__:
            raise ValueError(
                f"{name!r} is stored state rather than a color property. "
                f"Set {name.lstrip('_')!r} instead."
            )
        setattr(color, name, value)


def _carried_alpha(
    value: str | Sequence[int | float], func: Callable[[Any], HSLTuple]
) -> tuple[str, float] | None:
    """The alpha a positional colour value carries, and the format stating it.

    Every input that carries an alpha loses it on the way to HSL, so it is
    read back here, on that format's own scale.

    Parameters
    ----------
    value : str | Sequence[int | float]
        The value given as ``color``, already identified.
    func : Callable[[Any], HSLTuple]
        The converter :func:`identify_color` chose for it, which is what says
        which format the value turned out to be.

    Returns
    -------
    tuple[str, float] | None
        The format's name and its alpha in ``[0, 1]``, or ``None`` when the
        format carries no alpha.
    """
    if isinstance(value, str):
        if func is hexa2hsl:
            return "hex", hex2rgba(value)[3] / 255.0
        if func is css2hsl:
            return "css", css2hsla(value)[3] / 100.0
        return None
    if func is rgba2hsl:
        return "rgba", value[3] / 255.0
    if func is hsla2hsl:
        return "hsla", value[3] / 100.0
    return None


def _hard_light(backdrop: float, source: float) -> float:
    """The hard-light separable blend, on one channel in ``[0, 1]``."""
    if source <= 0.5:
        return backdrop * 2.0 * source
    doubled = 2.0 * source - 1.0
    return backdrop + doubled - backdrop * doubled


## The separable blend modes CSS defines, each taking the backdrop channel and
## the source channel. The non-separable ones -- hue, saturation, color,
## luminosity -- work on all three channels at once and are not here.
_BLEND_MODES: dict[str, Callable[[float, float], float]] = {
    "normal": lambda _backdrop, source: source,
    "multiply": lambda backdrop, source: backdrop * source,
    "screen": lambda backdrop, source: backdrop + source - backdrop * source,
    "overlay": lambda backdrop, source: _hard_light(source, backdrop),
    "darken": min,
    "lighten": max,
    "hard-light": _hard_light,
    "difference": lambda backdrop, source: abs(backdrop - source),
    "exclusion": lambda backdrop, source: backdrop + source - 2.0 * backdrop * source,
}


## The keyword colour inputs, each with the conversion that takes it to HSL.
## `color` and `pick_for` are not here: one is identified rather than named,
## and the other needs the picker arguments.
_KEYWORD_INPUTS: dict[str, Callable[[Any], Any]] = {
    "web": lambda value: web2hsl(value.strip().lower()),
    "hsl": lambda value: value,
    "hsla": hsla2hsl,
    "hslf": hslf2hsl,
    "hslaf": lambda value: hslf2hsl(value[:3]),
    "hsv": hsv2hsl,
    "xyz": xyz2hsl,
    "lab": lab2hsl,
    "lch": lch2hsl,
    "oklab": oklab2hsl,
    "oklch": oklch2hsl,
    "cmyk": cmyk2hsl,
    "yuv": yuv2hsl,
    "hex": hex2hsl,
    "hex_l": hex2hsl,
    "rgb": rgb2hsl,
    "rgba": rgba2hsl,
    "rgbf": rgbf2hsl,
    "rgbaf": rgbaf2hsl,
}

## The scale the fourth component is on, for the inputs that carry an alpha.
_KEYWORD_ALPHA_SCALES: dict[str, float] = {
    "hsla": 100.0,
    "rgba": 255.0,
    "hslaf": 1.0,
    "rgbaf": 1.0,
}


class Color:
    """Abstraction over a color with multi-format conversion properties.

    A color is held as HSL, which is bounded by sRGB, so the ``lab``, ``lch``,
    ``oklab``, ``oklch``, ``xyz`` and ``yuv`` inputs -- each of which can name
    a color sRGB cannot show -- are **clipped** to what sRGB can. That is
    silent, and it is not rare: 88% of the ``lab`` triples the range check
    accepts do not survive it. A clipped color is also indistinguishable
    afterwards from one that was always in gamut, since what is stored is the
    clipped value, so ask :func:`~colourings.conversions.in_srgb_gamut`
    beforehand rather than comparing afterwards.

    >>> Color(lab=(100, 120, -120)).lab
    LAB(lightness=95.85895978712477, a=8.621537162382786, b=-6.079793114528798)

    Every other input format is bounded by its own component ranges, so it is
    representable by construction and converts exactly.

    Parameters
    ----------
    color : str | Sequence[int | float] | Color | None, optional
        Generic color input in any supported format. Another ``Color`` has
        its value copied -- its components and its alpha, unless ``alpha``
        names one to use instead -- but not its ``equality`` strategy, which
        is a comparison policy rather than part of the color. Use
        ``copy.copy`` for a duplicate that keeps both.
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
        Explicit alpha value in ``[0, 1]``. It overrides the alpha of a
        ``Color`` passed as ``color``, but must agree with the one an
        ``rgba``, ``hsla``, ``rgbaf`` or ``hslaf`` value states.
    pick_for : object, optional
        Arbitrary value to pick a color for. The same value gives the same
        color, in this process and in any other, subject to the caveat on
        :func:`stable_key`.
    picker : ColorPicker, default=RGB_color_picker
        Picker function used with ``pick_for``.
    pick_key : PickKey, default=stable_key
        Key function used before passing values to ``picker``. Pass
        :func:`hash_or_str` for the old per-process behaviour.
    equality : ColorEquality, default=RGB_equivalence
        Equality strategy used by ``__eq__``. It always defaults to
        ``RGB_equivalence``, including when ``color`` is a ``Color`` carrying
        another strategy; see ``color`` above.
    **kwargs : Any
        Writable color properties to set once the color is built, such as
        ``lightness=0``. Each is assigned through its own setter, so it is
        validated like any other assignment and can raise. This is not a way
        to attach arbitrary attributes: ``Color`` defines ``__slots__``, so a
        name that is not one of its properties raises ``AttributeError``
        rather than becoming a new attribute. A subclass that does not
        redeclare ``__slots__`` has a ``__dict__``, and does accept any name.

    Raises
    ------
    ValueError
        Raised when none or more than one primary color input is provided.
    ValueError
        Raised when alpha is provided inconsistently across inputs.
    ValueError
        Raised when a keyword names one of the stored attributes, which would
        set it without the validation its property does.
    UnknownColorError
        Raised when the input does not match any supported color format.
    AttributeError
        Raised when a keyword is neither a writable property nor, on a
        subclass with a ``__dict__``, a name that can be attached.
    """

    ## Only these three are stored; every colour format below is a property
    ## computed from them. Declaring them as slots keeps a mistyped attribute an
    ## AttributeError instead of silently becoming a new attribute.
    __slots__ = ("_alpha", "_hsl", "equality")

    _hsl: HSLTuple  # internal representation
    _alpha: float
    equality: ColorEquality

    def __init__(
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
        pick_key: PickKey = stable_key,
        equality: ColorEquality = RGB_equivalence,
        **kwargs: Any,
    ):
        # checks
        ## Typed as Any because the dispatch below is dynamic: the values are
        ## the parameters, whose real types are on the signature.
        inputs: dict[str, Any] = {
            "color": color,
            "web": web,
            "hsl": hsl,
            "hsla": hsla,
            "hslf": hslf,
            "hslaf": hslaf,
            "hsv": hsv,
            "xyz": xyz,
            "lab": lab,
            "lch": lch,
            "oklab": oklab,
            "oklch": oklch,
            "cmyk": cmyk,
            "yuv": yuv,
            "hex": hex,
            "hex_l": hex_l,
            "rgb": rgb,
            "rgba": rgba,
            "rgbf": rgbf,
            "rgbaf": rgbaf,
            "pick_for": pick_for,
        }
        given = [name for name, value in inputs.items() if value is not None]
        if len(given) != 1:
            names = [f"{name!r}" for name in inputs]
            raise ValueError(
                f"Only one of {', '.join(names[:-1])} or {names[-1]} may be entered."
            )
        source = given[0]
        value = inputs[source]

        # convert to hsl
        if source == "color":
            if isinstance(value, str):
                value = value.strip().lower()
            func = identify_color(value)
            self.hsl = func(value)
            if isinstance(value, Color):
                ## Copied rather than reconciled: a Color always carries an
                ## alpha, so treating a disagreement as an error would reject
                ## `Color(other, alpha=0.5)` for every opaque `other`.
                if alpha is None:
                    alpha = value.alpha
            else:
                carried = _carried_alpha(value, func)
                if carried is not None:
                    alpha = _alpha_from(alpha, carried[1], carried[0])
        elif source == "pick_for":
            ## Taken as HSL rather than through `.web`, which quantised the
            ## picked colour to 8 bits per channel by way of a string.
            self.hsl = picker(pick_key(value)).hsl
        else:
            self.hsl = _KEYWORD_INPUTS[source](value)
            scale = _KEYWORD_ALPHA_SCALES.get(source)
            if scale is not None:
                alpha = _alpha_from(alpha, value[3] / scale, source)

        # set attributes
        self.equality = equality
        self.alpha = alpha if alpha is not None else 1.0
        _apply_property_keywords(self, kwargs)

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
        """Perceived brightness, from the channels as they are encoded.

        This is **not** luminance in the colorimetric sense, and it must not be
        used to judge contrast. It is the root mean square of the sRGB channels
        under BT.601's luma weights, taken without linearising them, which is a
        rough model of how bright a colour looks rather than of how much light
        it carries. The two part company by a lot: ``#777777`` is 0.467 here
        and 0.185 as :attr:`relative_luminance`.

        Kept, under this name, because it is what this property has always
        returned. For contrast, and for anything else that calls itself
        luminance elsewhere, use :attr:`relative_luminance` and
        :meth:`contrast_ratio`.

        Returns
        -------
        float
            Perceived brightness in ``[0, 1]``.
        """
        r, g, b = self.get_rgbf()
        return math.sqrt(0.299 * r**2 + 0.587 * g**2 + 0.114 * b**2)

    def get_is_dark(self) -> bool:
        """Whether white text reads better on this color than black.

        The threshold is where contrast against white equals contrast against
        black, so this is not a matter of taste: it agrees with
        :meth:`best_text_color` for every color in the sRGB cube.

        Returns
        -------
        bool
            ``True`` when the color is dark enough to want light text.
        """
        return self.relative_luminance < WCAG_LIGHT_DARK_CROSSOVER

    def get_is_light(self) -> bool:
        """The complement of :attr:`is_dark`.

        Returns
        -------
        bool
            ``True`` when the color wants dark text.
        """
        return not self.get_is_dark()

    def get_relative_luminance(self) -> float:
        """WCAG 2.x relative luminance, as
        :func:`~colourings.conversions.rgb2relative_luminance` computes it.

        Returns
        -------
        float
            Relative luminance in ``[0, 1]``.
        """
        return rgb2relative_luminance(self.rgb)

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
    relative_luminance = property(get_relative_luminance)
    is_dark = property(get_is_dark)
    is_light = property(get_is_light)

    def contrast_ratio(self, other: str | Sequence[int | float] | Color) -> float:
        """Compute the WCAG 2.x contrast ratio against another color.

        Symmetric, so which color is the text and which the background does
        not matter. WCAG 2.x asks for at least 4.5 for normal text and 3 for
        large text at AA, and 7 and 4.5 at AAA.

        Alpha plays no part, on either side. A contrast ratio is between two
        opaque colors, and a translucent one has no contrast of its own --
        it depends on whatever shows through it. Composite first, then ask.

        Parameters
        ----------
        other : str | Sequence[int | float] | Color
            The other color, in any supported input format.

        Returns
        -------
        float
            Contrast ratio in ``[1, 21]``.

        Examples
        --------
        >>> Color("black").contrast_ratio("white")
        21.0
        """
        return _contrast_ratio(self.rgb, Color(other).rgb)

    def is_readable(
        self,
        other: str | Sequence[int | float] | Color,
        level: str = "AA",
        size: str = "normal",
    ) -> bool:
        """Check whether text and background meet a WCAG 2.x contrast minimum.

        Symmetric, like :meth:`contrast_ratio`, so it does not matter which of
        the two colors is the text.

        The comparison is against the exact ratio, not a rounded one. A pair at
        4.4999 fails ``AA`` even though it would display as "4.50", which is
        where this can disagree with a tool that rounds before comparing.

        Parameters
        ----------
        other : str | Sequence[int | float] | Color
            The other color, in any supported input format.
        level : str, default="AA"
            Conformance level, ``"AA"`` or ``"AAA"``. Case-insensitive.
        size : str, default="normal"
            Text size, ``"normal"`` or ``"large"``. Large is 18pt, or 14pt
            bold. Case-insensitive.

        Returns
        -------
        bool
            ``True`` when the contrast ratio is at least the minimum for that
            level and size.

        Raises
        ------
        ValueError
            Raised when ``level`` and ``size`` are not a pair WCAG defines.

        Examples
        --------
        >>> Color("#767676").is_readable("white")
        True
        >>> Color("#777777").is_readable("white")
        False
        """
        wanted = (level.upper(), size.lower())
        if wanted not in WCAG_CONTRAST_MINIMUMS:
            pairs = ", ".join(
                f"{lvl}/{sz}" for lvl, sz in sorted(WCAG_CONTRAST_MINIMUMS)
            )
            raise ValueError(
                f"No WCAG minimum for level {level!r} at size {size!r}. "
                f"Choose one of: {pairs}."
            )
        return self.contrast_ratio(other) >= WCAG_CONTRAST_MINIMUMS[wanted]

    def best_text_color(
        self,
        candidates: Sequence[str | Sequence[int | float] | Color] = ("black", "white"),
    ) -> Color:
        """Pick the candidate that contrasts most with this color.

        Named for the common case -- this color is a background, and the
        answer is what to write on it -- but it is only a maximum of
        :meth:`contrast_ratio`, so it serves the reverse just as well.

        Contrast alone is the whole of the judgement. It says nothing about
        whether the result looks right, and a tie goes to whichever candidate
        came first, so the order of ``candidates`` is worth choosing.

        Parameters
        ----------
        candidates : Sequence[str | Sequence[int | float] | Color], default=("black", "white")
            Colors to choose between, in any supported input format.

        Returns
        -------
        Color
            The candidate with the highest contrast ratio against this color.

        Raises
        ------
        ValueError
            Raised when ``candidates`` is empty, or is a single string rather
            than a sequence of them.

        Examples
        --------
        >>> Color("navy").best_text_color()
        <Color white>
        """
        ## A str is a Sequence, so `candidates="white"` would otherwise be
        ## read as five one-letter colours.
        if isinstance(candidates, str):
            raise ValueError(
                f"`candidates` must be a sequence of colors, not the single "
                f"color {candidates!r}. Pass [{candidates!r}] to mean one."
            )
        colors = [Color(candidate) for candidate in candidates]
        if not colors:
            raise ValueError("`candidates` must contain at least one color.")
        return max(colors, key=self.contrast_ratio)

    def _with_hsl(self, hsl: Sequence[float]) -> Color:
        """Build a new color from HSL components, carrying this one's alpha."""
        return Color(hsl=hsl, alpha=self._alpha)

    def lighten(self, amount: float = 0.1, relative: bool = True) -> Color:
        """Return a lighter copy of this color.

        Moves HSL lightness, which is a geometric quantity rather than a
        perceptual one, so a step of a given size does not look the same size
        everywhere. When that matters, ``mix("white", amount)`` in ``oklab``
        lightens perceptually instead.

        Parameters
        ----------
        amount : float, default=0.1
            Size of the step, in ``[0, 1]``.
        relative : bool, default=True
            When ``True``, ``amount`` is a fraction of the lightness still
            available, so ``1.0`` gives white and nothing ever clips. When
            ``False``, it is a fraction of the whole range, added flat and
            clamped -- the behaviour of Sass's ``lighten()``.

        Returns
        -------
        Color
            A new color; this one is unchanged. Alpha is carried over.

        Raises
        ------
        ValueError
            Raised when ``amount`` is outside ``[0, 1]``.

        Examples
        --------
        >>> Color("#808080").lighten(0.5).hex_l
        '#bfbfbf'
        """
        _check_amount(amount)
        hue, saturation, lightness = self._hsl
        return self._with_hsl(
            HSLTuple(hue, saturation, _adjust(lightness, amount, 100.0, True, relative))
        )

    def darken(self, amount: float = 0.1, relative: bool = True) -> Color:
        """Return a darker copy of this color.

        The mirror of :meth:`lighten`, with ``relative`` meaning a fraction of
        the lightness there is to remove, so ``1.0`` gives black.

        Parameters
        ----------
        amount : float, default=0.1
            Size of the step, in ``[0, 1]``.
        relative : bool, default=True
            Whether ``amount`` is a fraction of the current lightness rather
            than of the whole range.

        Returns
        -------
        Color
            A new color; this one is unchanged. Alpha is carried over.

        Raises
        ------
        ValueError
            Raised when ``amount`` is outside ``[0, 1]``.
        """
        _check_amount(amount)
        hue, saturation, lightness = self._hsl
        return self._with_hsl(
            HSLTuple(
                hue, saturation, _adjust(lightness, amount, 100.0, False, relative)
            )
        )

    def saturate(self, amount: float = 0.1, relative: bool = True) -> Color:
        """Return a more saturated copy of this color.

        Parameters
        ----------
        amount : float, default=0.1
            Size of the step, in ``[0, 1]``.
        relative : bool, default=True
            Whether ``amount`` is a fraction of the saturation still available
            rather than of the whole range.

        Returns
        -------
        Color
            A new color; this one is unchanged. Alpha is carried over.

        Raises
        ------
        ValueError
            Raised when ``amount`` is outside ``[0, 1]``.
        """
        _check_amount(amount)
        hue, saturation, lightness = self._hsl
        return self._with_hsl(
            HSLTuple(hue, _adjust(saturation, amount, 100.0, True, relative), lightness)
        )

    def desaturate(self, amount: float = 0.1, relative: bool = True) -> Color:
        """Return a less saturated copy of this color.

        ``desaturate(1.0)`` gives a grey of the same HSL lightness, which is
        not the same grey as :meth:`grayscale`: this holds lightness, that
        holds luminance. For blue the two are far apart.

        Parameters
        ----------
        amount : float, default=0.1
            Size of the step, in ``[0, 1]``.
        relative : bool, default=True
            Whether ``amount`` is a fraction of the current saturation rather
            than of the whole range.

        Returns
        -------
        Color
            A new color; this one is unchanged. Alpha is carried over.

        Raises
        ------
        ValueError
            Raised when ``amount`` is outside ``[0, 1]``.
        """
        _check_amount(amount)
        hue, saturation, lightness = self._hsl
        return self._with_hsl(
            HSLTuple(
                hue, _adjust(saturation, amount, 100.0, False, relative), lightness
            )
        )

    def rotate_hue(self, degrees: float) -> Color:
        """Return a copy with the hue turned around the color wheel.

        Any angle is accepted and wrapped, so ``180`` and ``-180`` give the
        same color and ``360`` gives this one back.

        Parameters
        ----------
        degrees : float
            How far to turn, positive or negative.

        Returns
        -------
        Color
            A new color; this one is unchanged. Alpha is carried over.

        Examples
        --------
        >>> Color("red").rotate_hue(180).web
        'cyan'
        """
        hue, saturation, lightness = self._hsl
        return self._with_hsl(HSLTuple((hue + degrees) % 360.0, saturation, lightness))

    def grayscale(self) -> Color:
        """Return the grey with the same luminance as this color.

        Not ``desaturate(1.0)``, which holds HSL lightness instead and so
        changes how bright the color is. See
        :func:`~colourings.conversions.rgb2grayscale`.

        Returns
        -------
        Color
            A new color; this one is unchanged. Alpha is carried over.
        """
        return Color(rgb=rgb2grayscale(self.rgb), alpha=self._alpha)

    greyscale = grayscale

    def invert(self) -> Color:
        """Return the color with every RGB channel reflected about its range.

        Applied to the channels as encoded, which is what the CSS ``invert()``
        filter does. Alpha is left alone: inverting the color is not a request
        to change how opaque it is.

        Returns
        -------
        Color
            A new color; this one is unchanged. Alpha is carried over.

        Examples
        --------
        >>> Color("black").invert().web
        'white'
        """
        red, green, blue = self.rgb
        return Color(rgb=(255.0 - red, 255.0 - green, 255.0 - blue), alpha=self._alpha)

    def mix(
        self,
        other: str | Sequence[int | float] | Color,
        amount: float = 0.5,
        space: str = "oklab",
        longer: bool = False,
    ) -> Color:
        """Blend this color with another, in a chosen space.

        Unlike :func:`color_scale`, which defaults to ``hsl`` only because
        changing it would move every existing caller's output, this defaults to
        ``oklab``: it is new, so it can start on the space worth using.

        Alpha is blended too, linearly, as it is in a scale.

        Parameters
        ----------
        other : str | Sequence[int | float] | Color
            The color to blend towards, in any supported input format.
        amount : float, default=0.5
            How far to go, in ``[0, 1]``. ``0`` is this color and ``1`` is
            ``other``.
        space : str, default="oklab"
            Space to blend in, as described on :func:`color_scale`.
        longer : bool, default=False
            Whether to take the longer hue arc, in a space that has a hue.

        Returns
        -------
        Color
            A new color; this one is unchanged.

        Raises
        ------
        ValueError
            Raised when ``amount`` is outside ``[0, 1]``, when ``space`` is not
            supported, or when ``longer`` is asked for in a space with no hue.
        """
        _check_amount(amount)
        to_hsl, hue_index = _scale_space(space, longer)
        other = Color(other)
        start = list(getattr(self, space))
        end = list(getattr(other, space))
        if hue_index is not None:
            _unwrap_hue(start, end, hue_index, longer)
        values = [a + (b - a) * amount for a, b in zip(start, end, strict=True)]
        if hue_index is not None:
            values[hue_index] = (values[hue_index] * 360) % 360
        alpha = self._alpha + (other._alpha - self._alpha) * amount
        return Color(hsl=to_hsl(values), alpha=alpha)

    def to_css(self, form: str = "hex") -> str:
        """Write this color as CSS.

        Alpha is included only when the color is not opaque, so an opaque one
        comes out in the short form everyone already reads. The functional
        forms use the space-separated syntax with a slash before the alpha,
        which is what a browser serialises to.

        Parameters
        ----------
        form : str, default="hex"
            One of ``"hex"``, ``"rgb"``, ``"hsl"`` or ``"oklch"``.

        Returns
        -------
        str
            The color as CSS.

        Raises
        ------
        ValueError
            Raised when ``form`` is not one of the four.

        Examples
        --------
        >>> Color("red").to_css()
        '#f00'
        >>> Color("red", alpha=0.5).to_css("rgb")
        'rgb(255 0 0 / 0.5)'
        """
        return hsla2css(self._hsl, self._alpha, form)

    def complementary(self) -> Color:
        """Return the color opposite this one on the hue wheel.

        Returns
        -------
        Color
            A new color half a turn away.

        Examples
        --------
        >>> Color("red").complementary().web
        'cyan'
        """
        return self.rotate_hue(180.0)

    def analogous(self, angle: float = 30.0) -> tuple[Color, Color, Color]:
        """Return this color between its two neighbours on the hue wheel.

        Parameters
        ----------
        angle : float, default=30.0
            How far to either side, in degrees.

        Returns
        -------
        tuple[Color, Color, Color]
            The three colors in wheel order, this one in the middle.
        """
        return (self.rotate_hue(-angle), self.rotate_hue(0.0), self.rotate_hue(angle))

    def triadic(self) -> tuple[Color, Color, Color]:
        """Return the three colors evenly spaced around the hue wheel.

        Returns
        -------
        tuple[Color, Color, Color]
            This color and the two a third of a turn away in each direction.
        """
        return (self.rotate_hue(0.0), self.rotate_hue(120.0), self.rotate_hue(240.0))

    def tetradic(self) -> tuple[Color, Color, Color, Color]:
        """Return the four colors evenly spaced around the hue wheel.

        Returns
        -------
        tuple[Color, Color, Color, Color]
            This color and the three a quarter of a turn apart.
        """
        return (
            self.rotate_hue(0.0),
            self.rotate_hue(90.0),
            self.rotate_hue(180.0),
            self.rotate_hue(270.0),
        )

    def _repr_html_(self) -> str:
        """Render the color as a swatch, for a notebook.

        Jupyter calls this when a ``Color`` is the value of a cell, so a color
        shows as a color rather than as ``<Color #3d7ab8>``. Unlike
        :meth:`preview` it needs no GUI toolkit and does not block.

        A color that is not opaque is drawn over a checkerboard, so its alpha
        is visible rather than being quietly composited onto whatever the
        notebook's background happens to be.

        Returns
        -------
        str
            A fragment of HTML.
        """
        ## Nothing here is escaped because nothing here needs it: `web` is a
        ## colour name or a hex string, and the rest is generated numbers.
        label = self.web if self._alpha >= 1.0 else f"{self.web} / {self._alpha:g}"
        fill = self.to_css("rgb")
        if self._alpha >= 1.0:
            background = f"background:{fill}"
        else:
            squares = "#bbbbbb 25%, transparent 25%, transparent 75%, #bbbbbb 75%"
            background = (
                f"background-image:linear-gradient({fill},{fill}),"
                f"linear-gradient(45deg,{squares}),"
                "linear-gradient(45deg,#bbbbbb 25%,#ffffff 25%,"
                "#ffffff 75%,#bbbbbb 75%);"
                "background-size:100% 100%,12px 12px,12px 12px;"
                "background-position:0 0,0 0,6px 6px"
            )
        return (
            '<div style="display:inline-flex;align-items:center;gap:8px;'
            'font-family:monospace;font-size:12px">'
            f'<div title="{label}" style="width:28px;height:28px;'
            "border-radius:4px;border:1px solid rgba(128,128,128,0.4);"
            f'{background}"></div>'
            f"<span>{label}</span></div>"
        )

    def blend(
        self,
        backdrop: str | Sequence[int | float] | Color,
        mode: str = "normal",
        linear: bool = False,
    ) -> Color:
        """Composite this color over another, optionally through a blend mode.

        This color is the source and ``backdrop`` is what it is drawn on, the
        same way round as CSS: the result is what a browser shows for an
        element of this color over that background.

        Compositing happens on the channels as encoded, which is what CSS,
        canvas and every renderer do, and is **not** the physically correct
        answer -- light adds linearly and sRGB is not linear in light. The two
        are far apart: 50% red over white puts green at 127.5 encoded and at
        187.5 in linear light, sixty channel steps away. Pass ``linear=True``
        for the latter, which is what image processing wants and what no
        browser will agree with.

        Parameters
        ----------
        backdrop : str | Sequence[int | float] | Color
            The color underneath, in any supported input format.
        mode : str, default="normal"
            One of the separable CSS blend modes: ``"normal"``,
            ``"multiply"``, ``"screen"``, ``"overlay"``, ``"darken"``,
            ``"lighten"``, ``"hard-light"``, ``"difference"`` or
            ``"exclusion"``. An underscore reads the same as a hyphen.
        linear : bool, default=False
            Whether to composite in linear light rather than on the channels
            as encoded.

        Returns
        -------
        Color
            A new color; neither operand is changed. Its alpha is
            ``a + b * (1 - a)``, so an opaque backdrop gives an opaque result.

        Raises
        ------
        ValueError
            Raised when ``mode`` is not a separable blend mode.

        Examples
        --------
        >>> Color("red", alpha=0.5).blend("white").rgb
        RGB(red=255.0, green=127.5, blue=127.5)
        >>> Color("red").blend("cyan", "multiply").hex_l
        '#000000'
        """
        blend = _BLEND_MODES.get(mode.replace("_", "-").lower())
        if blend is None:
            raise ValueError(
                f"Unknown blend mode {mode!r}. Choose one of: "
                f"{', '.join(sorted(_BLEND_MODES))}."
            )
        backdrop = Color(backdrop)
        source_alpha, backdrop_alpha = self._alpha, backdrop._alpha
        alpha = source_alpha + backdrop_alpha * (1.0 - source_alpha)
        if alpha == 0.0:
            ## Nothing is visible, so no colour is more right than another.
            ## The source's is kept so that the result still says where it
            ## came from.
            return Color(hsl=self._hsl, alpha=0.0)

        encode = _linear_to_srgb if linear else lambda channel: channel
        decode = _srgb_to_linear if linear else lambda channel: channel
        channels = []
        for source, back in zip(self.rgbf, backdrop.rgbf, strict=True):
            source, back = decode(source), decode(back)
            ## The backdrop shows through the blend in proportion to how
            ## opaque it is: with nothing behind, there is nothing to blend
            ## with and the source passes through unchanged.
            blended = (1.0 - backdrop_alpha) * source + backdrop_alpha * blend(
                back, source
            )
            mixed = blended * source_alpha + back * backdrop_alpha * (
                1.0 - source_alpha
            )
            channels.append(min(max(encode(mixed / alpha), 0.0), 1.0))
        return Color(rgbf=channels, alpha=alpha)

    def over(
        self, backdrop: str | Sequence[int | float] | Color, linear: bool = False
    ) -> Color:
        """Composite this color over another, with no blend mode.

        The ``normal`` case of :meth:`blend`, and the one worth naming: it is
        what an alpha means.

        Parameters
        ----------
        backdrop : str | Sequence[int | float] | Color
            The color underneath, in any supported input format.
        linear : bool, default=False
            Whether to composite in linear light, as described on
            :meth:`blend`.

        Returns
        -------
        Color
            A new color; neither operand is changed.

        Examples
        --------
        >>> Color("red", alpha=0.5).over("white").rgb
        RGB(red=255.0, green=127.5, blue=127.5)
        """
        return self.blend(backdrop, "normal", linear)

    def delta_e(
        self, other: str | Sequence[int | float] | Color, metric: str = "ciede2000"
    ) -> float:
        """Measure how far this color is from another.

        Roughly, on the three L*a*b* metrics: 1 is the smallest difference a
        good eye can see side by side, 2 to 3 is noticeable, and above 5 they
        read as different colors. ``ok`` is on Oklab's own scale and its
        numbers are much smaller.

        Alpha plays no part. Two colors differing only in opacity are the same
        color at different strengths, and how far apart they look depends on
        what is behind them -- :meth:`over` first, then ask.

        Parameters
        ----------
        other : str | Sequence[int | float] | Color
            The color to compare with, in any supported input format.
        metric : str, default="ciede2000"
            One of ``"cie76"``, ``"cie94"``, ``"ciede2000"`` or ``"ok"``, as
            described in :mod:`colourings.difference`.

        Returns
        -------
        float
            The difference, on that metric's own scale, 0 for the same color.

        Raises
        ------
        ValueError
            Raised when ``metric`` is not one of the four.

        Examples
        --------
        >>> Color("black").delta_e("white")
        100.0
        >>> round(Color("red").delta_e("red"), 12)
        0.0
        """
        return hsl_difference(self._hsl, Color(other)._hsl, metric)

    def nearest_name(self, metric: str = "ok") -> str:
        """Find the named color closest to this one.

        Answers "what would I call this". An exact match gives that color's
        own name; anything else gives the nearest, however far away it is, so
        :meth:`delta_e` against it is worth checking before quoting it.

        Parameters
        ----------
        metric : str, default="ok"
            One of ``"cie76"``, ``"cie94"``, ``"ciede2000"`` or ``"ok"``. The
            default is perceptual and cheap, which matters because this runs
            over every name.

        Returns
        -------
        str
            The name, lowercase. :attr:`web` gives the canonical spelling for
            a colour that matches one exactly -- ``RebeccaPurple`` rather than
            ``rebeccapurple``.

        Raises
        ------
        ValueError
            Raised when ``metric`` is not one of the four.

        Examples
        --------
        >>> Color("#ff0001").nearest_name()
        'red'
        >>> Color("#123456").nearest_name()
        'midnightblue'
        """
        return nearest_named_hsl(self._hsl, metric)

    def range_to(
        self,
        value: str | Sequence[int | float] | Color,
        steps: int,
        longer: bool = False,
        space: str = "hsl",
    ) -> Generator[Color, None, None]:
        """Generate a color range from this color to another color.

        Alpha is interpolated along with the color, as described on
        :func:`color_scale`. The target supplies its own: a ``Color`` or a
        four-component sequence carries one, and every other form is opaque,
        having no way to say otherwise.

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

        This is the only part of the library that needs a GUI toolkit, so
        ``tkinter`` is imported here rather than at module scope. Being in the
        standard library does not make it free to import, nor guarantee it is
        installed: it pulls in the ``_tkinter`` extension and links Tcl/Tk,
        which costs around three times what importing the rest of this package
        does, and most distributions ship it as a separate package that a
        minimal install will not have. Importing it at module scope would make
        ``import colourings`` slower for everyone and impossible on a headless
        box, in exchange for a debugging aid most callers never reach for.

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

        Raises
        ------
        ImportError
            Raised when ``tkinter`` is not installed, naming the package that
            provides it.
        TypeError
            Raised when either dimension is not a number.
        """
        try:
            import tkinter
        except ImportError as error:
            raise ImportError(
                "Color.preview() needs tkinter, which is not installed. It "
                "ships with CPython on Windows and macOS, but most Linux "
                "distributions package it separately: install python3-tkinter "
                "on the Red Hat family, or python3-tk on Debian and Ubuntu. "
                "Nothing else in colourings needs it."
            ) from error

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
        root.title(f"{self!s} preview")
        root.mainloop()

    def __str__(self) -> str:
        return f"{self.web}"

    def __repr__(self) -> str:
        return f"<Color {self.web}>"

    def equals(
        self,
        other: str | Sequence[int | float] | Color,
        equality: ColorEquality = RGB_equivalence,
    ) -> bool:
        """Compare with a named strategy, ignoring what either color carries.

        A well-behaved comparison, which ``==`` is not: it applies one
        strategy to both operands, so it is reflexive, symmetric and
        transitive whenever that strategy is -- and both built-in strategies
        are. Reach for this wherever the answer matters, and for ``==``
        wherever the default is fine.

        Parameters
        ----------
        other : str | Sequence[int | float] | Color
            The color to compare with, in any supported input format.
        equality : ColorEquality, default=RGB_equivalence
            The strategy to apply. Deliberately not either operand's own: the
            point is an answer that does not depend on how they were built.

        Returns
        -------
        bool
            Whether that strategy considers the two equal.

        Examples
        --------
        >>> Color("red").equals("#f00")
        True
        >>> Color("red").equals("#f00", HSL_equivalence)
        True
        """
        return equality(self, Color(other))

    def __eq__(self, other: object) -> bool:
        """Compare two colors using their equality strategies.

        Both operands are consulted, because the strategy is per-instance and
        consulting only ``self`` made ``==`` asymmetric: ``a == b`` and
        ``b == a`` could disagree when the two carried different strategies.
        When they share one, which is the usual case, the result is unchanged.

        Consulting both costs more than it looks, and all three of these bite
        only once a colour carries something other than the default:

        - **Not transitive across mixed strategies.** With ``a`` and ``c``
          strict and ``b`` loose, ``a == b`` and ``b == c`` can both hold
          while ``a == c`` does not. ``set``, ``dict``, ``in`` and
          ``assertEqual`` all assume otherwise.
        - **A strict strategy is unenforceable unless both operands carry
          it**, since the looser one only has to agree once for ``or`` to be
          satisfied.
        - **A strategy looser than ``hex_l`` breaks the hash contract**, so
          ``b in {a}`` can be ``False`` where ``a == b``. See :meth:`__hash__`.

        :meth:`equals` has none of these, taking the strategy as an argument
        rather than from the operands.

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
        render the same ``hex_l``.

        Only a strategy *looser* than ``hex_l`` breaks the contract, and it
        breaks it properly: two colors that compare equal can hash apart, so
        ``b in {a}`` is ``False`` where ``a == b``, and a set holds both. A
        *stricter* strategy is fine -- ``HSL_equivalence`` lets two colors
        share a hash while comparing unequal, which is an ordinary collision
        that ``set`` and ``dict`` resolve by comparing.

        ``Color`` is mutable, so the hash follows the current value. Do not
        mutate a color while it is held in a set or used as a dict key.

        Returns
        -------
        int
            Hash of the color's ``hex_l`` value.
        """
        return hash(self.hex_l)


Colour = Color


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


## The accessors were called ``HSL``, ``RGB`` and ``HEX`` before 2.0. Reached
## through the module ``__getattr__`` rather than left as globals, so that the
## old spelling still works, says what to use instead, and -- crucially --
## cannot be confused with the tuple types of the same name.
_RENAMED_IN_2_0 = {
    "HSL": "NAMED_HSL",
    "RGB": "NAMED_RGB",
    "HEX": "NAMED_HEX",
}


def __getattr__(name: str) -> Any:
    """Resolve the pre-2.0 names of the named-colour accessors.

    Parameters
    ----------
    name : str
        Attribute being looked up on the module.

    Returns
    -------
    Any
        The renamed accessor, for one of the three old names.

    Raises
    ------
    AttributeError
        Raised for any other name, as normal attribute lookup would.
    """
    renamed = _RENAMED_IN_2_0.get(name)
    if renamed is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    reason = (
        f"which shadowed the {name} tuple type in colourings.definitions"
        if name in ("HSL", "RGB")
        else "for consistency with the other two"
    )
    warnings.warn(
        f"colourings.colour.{name} was renamed to {renamed} in 2.0, {reason}.",
        DeprecationWarning,
        stacklevel=2,
    )
    return globals()[renamed]
