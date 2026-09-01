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
from .conversions import (
    contrast_ratio as _contrast_ratio,
)
from .definitions import CMYK as CMYKTuple

## The colour tuple types are aliased because this module already exposes
## ``HSL`` and ``RGB`` as the named-colour accessor singletons defined below.
from .definitions import COLOR_NAME_TO_RGB, WCAG_CONTRAST_MINIMUMS, linspace
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

    Alpha is interpolated alongside the colour, linearly and independently of
    ``space``, since it is part of no colour space. A scale between opaque
    colours is therefore unchanged, and one between colours of differing
    opacity fades between them rather than coming out opaque throughout.

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
        ## Alpha rides alongside the space's channels rather than being one of
        ## them. It belongs to no colour space -- it is linear in every one, so
        ## the space argument does not apply to it -- and each `to_hsl` above
        ## takes exactly three components.
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


def _alpha_from(given: float | None, carried: float, format: str) -> float:
    """Reconcile an ``alpha`` argument with the alpha a color value carries.

    Parameters
    ----------
    given : float | None
        Value passed as the ``alpha`` keyword, if any.
    carried : float
        Alpha carried by the color value, already scaled to ``[0, 1]``.
    format : str
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
            f"Alpha value defined twice and does not have the same value: alpha={given} and alpha of {format}={carried}"
        )
    return carried


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
    elif isinstance(color, Sequence) and is_rgba(color):
        return rgba2hsl
    elif isinstance(color, Sequence) and is_hsla(color):
        return hsla2hsl
    else:
        raise UnknownColorError("Cannot identify color.")


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
        Arbitrary value used to deterministically pick a color.
    picker : ColorPicker, default=RGB_color_picker
        Picker function used with ``pick_for``.
    pick_key : PickKey, default=hash_or_str
        Key function used before passing values to ``picker``.
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
            ## Every input that carries an alpha loses it in the conversion to
            ## HSL, so recover it here on that input's own scale. Without this
            ## a positional colour would silently come out opaque while the
            ## equivalent keyword form kept its alpha.
            if isinstance(color, Color):
                ## A Color is copied rather than reconciled. The four-component
                ## sequences below state an alpha explicitly, so an `alpha` that
                ## disagrees with one is a contradiction worth reporting; a
                ## Color instead always carries an alpha, defaulting to 1.0
                ## when nobody chose it, so treating a disagreement as an error
                ## would reject `Color(other, alpha=0.5)` -- the ordinary way to
                ## restate a colour's opacity -- for every opaque `other`.
                if alpha is None:
                    alpha = color.alpha
            ## The isinstance check is redundant at runtime, since only a
            ## sequence is ever identified as one of these, but it is what
            ## narrows `color` away from `str` and `Color` for the subscript.
            elif isinstance(color, Sequence) and not isinstance(color, str):
                if func is rgba2hsl:
                    alpha = _alpha_from(alpha, color[3] / 255.0, "rgba")
                elif func is hsla2hsl:
                    alpha = _alpha_from(alpha, color[3] / 100.0, "hsla")
        elif web is not None:
            web = web.lower()
            self.hsl = web2hsl(web)
        elif hsl is not None:
            self.hsl = hsl
        elif hsla is not None:
            self.hsl = hsla2hsl(hsla)
            alpha = _alpha_from(alpha, hsla[3] / 100.0, "hsla")
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
            self.hsl = hslf2hsl(hslaf[:3])
            alpha = _alpha_from(alpha, hslaf[3], "hslaf")
        elif hex is not None:
            self.hsl = hex2hsl(hex)
        elif hex_l is not None:
            self.hsl = hex2hsl(hex_l)
        elif rgb is not None:
            self.hsl = rgb2hsl(rgb)
        elif rgba is not None:
            self.hsl = rgba2hsl(rgba)
            alpha = _alpha_from(alpha, rgba[3] / 255.0, "rgba")
        elif rgbf is not None:
            self.hsl = rgbf2hsl(rgbf)
        elif rgbaf is not None:
            self.hsl = rgbaf2hsl(rgbaf)
            alpha = _alpha_from(alpha, rgbaf[3], "rgbaf")
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
            ## The stored attributes are reachable by name, and assigning one
            ## here would skip the property that guards it: `_hsl` would take
            ## any three objects and `_alpha` any number, leaving a colour that
            ## fails later, somewhere else. `__slots__` exists to turn a
            ## mistyped attribute into an AttributeError; letting keywords
            ## write the slots would undo that for the two names it protects.
            if k in Color.__slots__:
                raise ValueError(
                    f"{k!r} is stored state rather than a color property. "
                    f"Set {k.lstrip('_')!r} instead."
                )
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
        ## A str is a Sequence, so `candidates="white"` would otherwise be read
        ## as the four colours "w", "h", "i", "t", "e" and fail on the first.
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

    ## British spelling, as with Colour and colour_scale.
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
