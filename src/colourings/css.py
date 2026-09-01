"""Reading and writing the color syntax CSS uses.

The hexadecimal and named forms are older than CSS and live with the other
conversions. What is here is the functional notation -- ``rgb(255 0 0)``,
``hsl(0 100% 50%)``, ``oklch(0.63 0.26 29)`` -- the ``transparent`` keyword,
and the serialiser that writes those forms back out.

Both the comma-separated and the space-separated argument styles are accepted,
since both are current: ``rgb(255, 0, 0)`` is what every existing stylesheet
says and ``rgb(255 0 0 / 50%)`` is what CSS Color 4 writes. Output is always
the space-separated form, which is what a browser itself serialises to.

A value outside the range its format allows is an error rather than being
clamped, which is where this parts company with a browser: CSS says
``rgb(300 0 0)`` is red, and here it does not parse. Silently correcting a
color into a different color is the behaviour this library avoids elsewhere,
and reading a stylesheet is not a reason to start.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence

## `_cached` rather than lru_cache, so `clear_caches` reaches these too.
from .conversions import (
    _cached,
    hsl2oklch,
    hsl2rgb,
    lab2hsl,
    lch2hsl,
    oklab2hsl,
    oklch2hsl,
    rgb2hex,
    rgb2hsl,
    rgba2hex,
)
from .definitions import HSL, HSLA
from .errors import InvalidColorError
from .identify import is_hsl

CSS_FUNCTION = re.compile(r"([a-z]+)\(\s*([^()]*?)\s*\)")

_NUMBER = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
_NUMBER_TOKEN = re.compile(rf"{_NUMBER}")
_PERCENT_TOKEN = re.compile(rf"({_NUMBER})%")
_ANGLE_TOKEN = re.compile(rf"({_NUMBER})(deg|grad|rad|turn)?")

## One turn in each unit CSS accepts for an angle.
_ANGLE_TURN = {"deg": 360.0, "grad": 400.0, "rad": 2.0 * math.pi, "turn": 1.0}


def _number(token: str) -> float:
    """Read a plain number, rejecting a percentage.

    Parameters
    ----------
    token : str
        One argument of a color function.

    Returns
    -------
    float
        The value.

    Raises
    ------
    InvalidColorError
        Raised when the token is not a plain number.
    """
    if not _NUMBER_TOKEN.fullmatch(token):
        raise InvalidColorError(f"Expected a number, not {token!r}.")
    return float(token)


def _scaled(reference: float) -> Callable[[str], float]:
    """Build a reader for a component that may be written as a percentage.

    Parameters
    ----------
    reference : float
        The value ``100%`` stands for.

    Returns
    -------
    Callable[[str], float]
        A reader that takes a number as it is and scales a percentage.
    """

    def read(token: str) -> float:
        percent = _PERCENT_TOKEN.fullmatch(token)
        if percent:
            return float(percent.group(1)) / 100.0 * reference
        return _number(token)

    return read


def _angle(token: str) -> float:
    """Read an angle in any of the units CSS allows, as degrees in ``[0, 360)``.

    Parameters
    ----------
    token : str
        One argument of a color function.

    Returns
    -------
    float
        The angle in degrees, wrapped into ``[0, 360)``.

    Raises
    ------
    InvalidColorError
        Raised when the token is not an angle.
    """
    match = _ANGLE_TOKEN.fullmatch(token)
    if not match:
        raise InvalidColorError(f"Expected an angle, not {token!r}.")
    value, unit = float(match.group(1)), match.group(2) or "deg"
    return value / _ANGLE_TURN[unit] * 360.0 % 360.0


def _hsl_components(values: Sequence[float]) -> HSL:
    """Take three HSL components as they are, having checked their ranges."""
    if not is_hsl(values):
        raise InvalidColorError(f"Input is not an HSL type: {tuple(values)}.")
    return HSL(*values)


## Chroma and the a/b axes take a number only: CSS gives them percentage
## reference ranges that differ per function, and a wrong one would misread a
## colour rather than reject it.
_CSS_FUNCTIONS: dict[
    str,
    tuple[
        tuple[Callable[[str], float], ...],
        Callable[[Sequence[float]], HSL],
    ],
] = {
    "rgb": ((_scaled(255.0), _scaled(255.0), _scaled(255.0)), rgb2hsl),
    "rgba": ((_scaled(255.0), _scaled(255.0), _scaled(255.0)), rgb2hsl),
    "hsl": ((_angle, _scaled(100.0), _scaled(100.0)), _hsl_components),
    "hsla": ((_angle, _scaled(100.0), _scaled(100.0)), _hsl_components),
    "lab": ((_scaled(100.0), _number, _number), lab2hsl),
    "lch": ((_scaled(100.0), _number, _angle), lch2hsl),
    "oklab": ((_scaled(1.0), _number, _number), oklab2hsl),
    "oklch": ((_scaled(1.0), _number, _angle), oklch2hsl),
}

_read_alpha = _scaled(1.0)


def is_css(color: object) -> bool:
    """Check whether a value is CSS color syntax this module can read.

    Answers on the shape alone -- a recognised function name, or the
    ``transparent`` keyword. ``rgb(nonsense)`` is CSS syntax and does not
    parse, and saying so is more use than reporting it as an unknown format.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when the value is a color function this module handles, or
        ``transparent``.

    Examples
    --------
    >>> is_css("rgb(255 0 0)")
    True
    >>> is_css("#ff0000")
    False
    """
    if not isinstance(color, str):
        return False
    text = color.strip().lower()
    if text == "transparent":
        return True
    match = CSS_FUNCTION.fullmatch(text)
    return match is not None and match.group(1) in _CSS_FUNCTIONS


def _split_arguments(arguments: str) -> tuple[list[str], str | None]:
    """Separate a function's components from the alpha written after a slash.

    Parameters
    ----------
    arguments : str
        Everything between the parentheses.

    Returns
    -------
    tuple[list[str], str | None]
        The component tokens, and the alpha token when one was given after a
        slash. An alpha given as a trailing argument instead is left among the
        components for the caller to take, since only it knows how many
        components to expect.
    """
    head, slash, tail = arguments.partition("/")
    alpha = tail.strip() if slash else None
    tokens = head.split(",") if "," in head else head.split()
    return [token.strip() for token in tokens if token.strip()], alpha


@_cached
def css2hsla(css: str) -> HSLA:
    """Convert CSS color syntax to HSL with an alpha.

    Parameters
    ----------
    css : str
        A color function, like ``rgb(255 0 0)`` or ``hsl(0deg 100% 50% / 0.5)``,
        or the keyword ``transparent``. Case and surrounding space do not
        matter.

    Returns
    -------
    HSLA
        HSLA tuple, with alpha on its own ``[0, 100]`` scale.

    Raises
    ------
    InvalidColorError
        Raised when the string is not a color function this module reads, when
        it has the wrong number of components, or when a component is not the
        kind of value that position takes.

    Examples
    --------
    >>> css2hsla("rgb(255 0 0)")
    HSLA(hue=0.0, saturation=100.0, lightness=50.0, alpha=100.0)
    >>> css2hsla("transparent")
    HSLA(hue=0.0, saturation=0.0, lightness=0.0, alpha=0.0)
    """
    text = css.strip().lower()
    if text == "transparent":
        return HSLA(0.0, 0.0, 0.0, 0.0)

    match = CSS_FUNCTION.fullmatch(text)
    if match is None or match.group(1) not in _CSS_FUNCTIONS:
        raise InvalidColorError(f"Not a CSS color function: {css!r}.")
    name, arguments = match.group(1), match.group(2)
    readers, to_hsl = _CSS_FUNCTIONS[name]

    tokens, alpha_token = _split_arguments(arguments)
    ## `rgba(r, g, b, a)` puts the alpha last instead of after a slash.
    if alpha_token is None and len(tokens) == len(readers) + 1:
        alpha_token = tokens.pop()
    if len(tokens) != len(readers):
        raise InvalidColorError(
            f"{name}() takes {len(readers)} components and an optional alpha, "
            f"but {len(tokens)} were given in {css!r}."
        )

    values = [read(token) for read, token in zip(readers, tokens, strict=True)]
    alpha = 1.0 if alpha_token is None else _read_alpha(alpha_token)
    if not 0.0 <= alpha <= 1.0:
        raise InvalidColorError(f"Alpha must be between 0 and 1, not {alpha}.")

    hue, saturation, lightness = to_hsl(values)
    return HSLA(hue, saturation, lightness, alpha * 100.0)


@_cached
def css2hsl(css: str) -> HSL:
    """Convert CSS color syntax to HSL, dropping any alpha.

    Parameters
    ----------
    css : str
        A color function or the keyword ``transparent``.

    Returns
    -------
    HSL
        HSL tuple. :func:`css2hsla` keeps the alpha.
    """
    hue, saturation, lightness, _ = css2hsla(css)
    return HSL(hue, saturation, lightness)


def _trim(value: float, places: int) -> str:
    """Write a number without trailing zeros, and without a negative zero.

    Only the fractional part is stripped. Stripping unconditionally turns the
    channel value 250 into "25", which is a colour rather than a rounding.
    """
    text = f"{value:.{places}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("", "-0", "-") else text


def hsla2css(
    hsl: Sequence[int | float], alpha: int | float = 1.0, form: str = "hex"
) -> str:
    """Write a color as CSS, in one of the forms CSS understands.

    Alpha is written only when the color is not opaque, so an opaque color
    comes out in the short form everyone already reads.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL components as ``(h, s, l)``.
    alpha : int | float, default=1.0
        Alpha in the ``[0, 1]`` range.
    form : str, default="hex"
        One of ``"hex"``, ``"rgb"``, ``"hsl"`` or ``"oklch"``.

    Returns
    -------
    str
        The color as CSS. The functional forms use the space-separated syntax
        with a slash before the alpha, which is what a browser serialises to.

    Raises
    ------
    ValueError
        Raised when ``form`` is not one of the four.

    Examples
    --------
    >>> hsla2css((0, 100, 50), 1.0)
    '#f00'
    >>> hsla2css((0, 100, 50), 0.5, "rgb")
    'rgb(255 0 0 / 0.5)'
    >>> hsla2css((0, 100, 50), 1.0, "oklch")
    'oklch(0.62796 0.25768 29.23389)'
    """
    if form not in ("hex", "rgb", "hsl", "oklch"):
        raise ValueError(
            f"Unknown CSS form {form!r}. Choose one of: hex, hsl, oklch, rgb."
        )
    opaque = alpha >= 1.0
    if form == "hex":
        red, green, blue = hsl2rgb(hsl)
        if opaque:
            return rgb2hex((red, green, blue))
        return rgba2hex((red, green, blue, alpha * 255.0))

    if form == "rgb":
        body = " ".join(_trim(channel, 0) for channel in hsl2rgb(hsl))
    elif form == "hsl":
        hue, saturation, lightness = hsl
        body = f"{_trim(hue, 2)} {_trim(saturation, 2)}% {_trim(lightness, 2)}%"
    else:
        lightness, chroma, hue = hsl2oklch(hsl)
        ## Five places, not the usual three: oklch chroma spans only 0 to 0.4,
        ## so three is coarser than an 8-bit channel, and four still loses the
        ## colours sitting on the gamut boundary.
        body = f"{_trim(lightness, 5)} {_trim(chroma, 5)} {_trim(hue, 5)}"
    tail = "" if opaque else f" / {_trim(alpha, 4)}"
    return f"{form}({body}{tail})"
