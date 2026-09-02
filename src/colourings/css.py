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
    LINEAR_A98_TO_LINEAR_SRGB,
    LINEAR_P3_TO_LINEAR_SRGB,
    LINEAR_REC2020_TO_LINEAR_SRGB,
    XYZ_D65_TO_LINEAR_SRGB,
    _a98_to_linear,
    _cached,
    _linear_to_srgb,
    _matrix_apply,
    _rec2020_to_linear,
    _srgb_to_linear,
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


## The reference each percentage stands for, taken from the tables in CSS
## Color 4 -- they differ per function, which is why these are spelled out here
## rather than shared. `_scaled` handles the negative end for free, since
## -100% is -100 / 100 * reference.
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
    "lab": ((_scaled(100.0), _scaled(125.0), _scaled(125.0)), lab2hsl),
    "lch": ((_scaled(100.0), _scaled(150.0), _angle), lch2hsl),
    "oklab": ((_scaled(1.0), _scaled(0.4), _scaled(0.4)), oklab2hsl),
    "oklch": ((_scaled(1.0), _scaled(0.4), _angle), oklch2hsl),
}

_read_alpha = _scaled(1.0)


## `color-mix()` is parsed apart from the functions in `_CSS_FUNCTIONS`, for
## two reasons. It takes whole colours rather than components, so its arguments
## nest and `CSS_FUNCTION`'s body pattern -- which excludes parentheses --
## cannot describe them. And resolving those colours needs the whole of
## `identify_color`, which lives a module above this one, so what is here is
## the syntax and the arithmetic on the percentages, and nothing that turns a
## string into a colour.
COLOR_MIX = re.compile(r"color-mix\((?P<arguments>.*)\)", re.S)

## The hue-interpolation methods CSS Color 4 section 13.5 defines. `shorter` is
## the default when none is written.
CSS_HUE_METHODS = ("shorter", "longer", "increasing", "decreasing")


def _split_outside_parentheses(text: str, separators: str) -> list[str]:
    """Split on separators that are not inside parentheses.

    A naive split cannot be used on `color-mix()`: its arguments may be colour
    functions, and `color-mix(in oklab, rgb(255 0 0) 40%, blue)` has commas and
    spaces belonging to the inner function.

    Parameters
    ----------
    text : str
        The text to split.
    separators : str
        Characters to split on, each considered only at nesting depth zero.

    Returns
    -------
    list[str]
        The pieces, stripped, with empty ones dropped.

    Raises
    ------
    InvalidColorError
        Raised when the parentheses do not balance.
    """
    pieces, depth, start = [], 0, 0
    for index, character in enumerate(text):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise InvalidColorError(f"Unbalanced parentheses in {text!r}.")
        elif depth == 0 and character in separators:
            pieces.append(text[start:index])
            start = index + 1
    if depth:
        raise InvalidColorError(f"Unbalanced parentheses in {text!r}.")
    pieces.append(text[start:])
    return [piece.strip() for piece in pieces if piece.strip()]


def is_color_mix(color: object) -> bool:
    """Check whether a value is a ``color-mix()`` function.

    Answers on the shape alone, like :func:`is_css`, so that a malformed one
    reaches the parser and gets a specific complaint.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when the value is a ``color-mix()`` call.

    Examples
    --------
    >>> is_color_mix("color-mix(in oklab, red, blue)")
    True
    >>> is_color_mix("color-mixture(red, blue)")
    False
    """
    if not isinstance(color, str):
        return False
    return COLOR_MIX.fullmatch(color.strip().lower()) is not None


def read_mix_method(token: str) -> tuple[str, str] | None:
    """Read a ``<color-interpolation-method>``, or say it is not one.

    Parameters
    ----------
    token : str
        The first comma-separated argument of ``color-mix()``, which is the
        interpolation method when it begins with ``in``, and a colour
        otherwise.

    Returns
    -------
    tuple[str, str] | None
        The space and the hue-interpolation method, or None when the token is
        not an interpolation method at all.

    Raises
    ------
    InvalidColorError
        Raised when the token begins with ``in`` but is not a method this
        module can read.
    """
    words = token.split()
    if not words or words[0] != "in":
        return None
    if len(words) == 2:
        return words[1], "shorter"
    ## `in oklch longer hue` -- the trailing `hue` is part of the grammar.
    if len(words) == 4 and words[3] == "hue" and words[2] in CSS_HUE_METHODS:
        return words[1], words[2]
    raise InvalidColorError(
        f"Cannot read {token!r} as a color interpolation method. It takes "
        f"'in <space>', optionally followed by one of "
        f"{', '.join(CSS_HUE_METHODS)} and the word 'hue'."
    )


def read_mix_item(token: str) -> tuple[str, float | None]:
    """Split one ``color-mix()`` argument into its colour and its percentage.

    The grammar joins the two with ``&&``, so either order is allowed.

    Parameters
    ----------
    token : str
        One comma-separated argument.

    Returns
    -------
    tuple[str, float | None]
        The colour as written, and its percentage when one was given.

    Raises
    ------
    InvalidColorError
        Raised when the argument is not one colour with at most one
        percentage, or the percentage is outside ``[0, 100]``.
    """
    percentages: list[tuple[str, float]] = []
    colours: list[str] = []
    for piece in _split_outside_parentheses(token, " 	"):
        match = _PERCENT_TOKEN.fullmatch(piece)
        if match:
            percentages.append((piece, float(match.group(1))))
        else:
            colours.append(piece)
    if len(colours) != 1 or len(percentages) > 1:
        raise InvalidColorError(
            f"{token!r} is not one color with an optional percentage."
        )
    if not percentages:
        return colours[0], None
    written, amount = percentages[0]
    if not 0.0 <= amount <= 100.0:
        raise InvalidColorError(
            f"A color-mix() percentage must be between 0% and 100%, not {written!r}."
        )
    return colours[0], amount


def normalize_mix_percentages(
    percentages: Sequence[float | None],
) -> tuple[list[float], float]:
    """Fill in and rescale the percentages of a ``color-mix()``.

    CSS Values 5's algorithm, with the "forced normalization" flag that
    ``color-mix()`` sets. Reproduces every worked example in CSS Color 5
    section 3.2, including the one the leftover rule exists for:
    ``purple 30%, plum 30%`` is a half-and-half mix at alpha 0.6, while
    ``purple 80%, plum 80%`` is the same mix left opaque.

    Parameters
    ----------
    percentages : Sequence[float | None]
        One per colour, ``None`` where none was written.

    Returns
    -------
    tuple[list[float], float]
        The weights, summing to 100 or to 0, and the leftover percentage. The
        result's alpha is multiplied by ``1 - leftover / 100``.
    """
    given = [value for value in percentages if value is not None]
    ## Clamped, so that `80%, 80%` leaves nothing over.
    specified = min(sum(given), 100.0) if given else 0.0
    omitted = len(percentages) - len(given)
    share = (100.0 - specified) / omitted if omitted else 0.0
    filled = [share if value is None else value for value in percentages]

    ## The leftover is measured before rescaling, which is what makes
    ## `30%, 30%` translucent and `80%, 80%` not.
    total = sum(filled)
    leftover = 100.0 - total if total < 100.0 else 0.0
    if total > 0.0:
        filled = [value * 100.0 / total for value in filled]
    return filled, leftover


## How each `color()` space reaches linear sRGB. The matrices and transfer
## functions live with the other conversions; what is here is only which
## keyword means which of them.
_PREDEFINED_SPACES: dict[str, Callable[[Sequence[float]], Sequence[float]]] = {
    "srgb": lambda values: [_srgb_to_linear(value) for value in values],
    "srgb-linear": list,
    "display-p3": lambda values: _matrix_apply(
        LINEAR_P3_TO_LINEAR_SRGB, [_srgb_to_linear(value) for value in values]
    ),
    "a98-rgb": lambda values: _matrix_apply(
        LINEAR_A98_TO_LINEAR_SRGB, [_a98_to_linear(value) for value in values]
    ),
    "rec2020": lambda values: _matrix_apply(
        LINEAR_REC2020_TO_LINEAR_SRGB, [_rec2020_to_linear(value) for value in values]
    ),
    "xyz": lambda values: _matrix_apply(XYZ_D65_TO_LINEAR_SRGB, values),
    "xyz-d65": lambda values: _matrix_apply(XYZ_D65_TO_LINEAR_SRGB, values),
}

## What is left of the specification's list. Both are relative to D50, so
## reading them needs a chromatic adaptation this package does not have --
## new machinery rather than another constant. Named here so that asking for
## one says what is missing rather than that the color cannot be identified.
_UNSUPPORTED_SPACES = ("prophoto-rgb", "xyz-d50")

## Every function name this module reads. `color()` is not in `_CSS_FUNCTIONS`
## because it takes a space keyword where the others take a first component, so
## it is read separately -- but a caller asking "is this CSS?" should not have
## to know that.
CSS_FUNCTION_NAMES = frozenset(_CSS_FUNCTIONS) | {"color"}


def _predefined_color(tokens: list[str], alpha: float) -> HSLA:
    """Read a ``color()`` function's arguments.

    Parameters
    ----------
    tokens : list[str]
        The space keyword followed by its three components.
    alpha : float
        Alpha in ``[0, 1]``, already read.

    Returns
    -------
    HSLA
        HSLA tuple, with alpha on its own ``[0, 100]`` scale.

    Raises
    ------
    InvalidColorError
        Raised when the space is unknown or unsupported, or the components are
        not three numbers or percentages.
    """
    if not tokens:
        raise InvalidColorError("color() takes a color space and three components.")
    space, components = tokens[0], tokens[1:]
    if space in _UNSUPPORTED_SPACES:
        raise InvalidColorError(
            f"color() cannot read {space!r} yet. This package converts "
            f"{', '.join(sorted(_PREDEFINED_SPACES))}."
        )
    if space not in _PREDEFINED_SPACES:
        raise InvalidColorError(
            f"{space!r} is not a predefined color space. color() takes "
            f"{', '.join(sorted(_PREDEFINED_SPACES))}."
        )
    if len(components) != 3:
        raise InvalidColorError(
            f"color({space} ...) takes 3 components, but {len(components)} were given."
        )

    ## Numbers and percentages both, with 100% meaning 1 in every one of these
    ## spaces -- which is the one thing CSS makes uniform here.
    values = [_scaled(1.0)(component) for component in components]
    linear = _PREDEFINED_SPACES[space](values)
    ## Out of the sRGB gamut is clipped, as everywhere else in this package.
    ## `in_srgb_gamut` is the way to ask before trusting the answer.
    channels = [min(max(_linear_to_srgb(component), 0.0), 1.0) for component in linear]
    hue, saturation, lightness = rgb2hsl([channel * 255.0 for channel in channels])
    return HSLA(hue, saturation, lightness, alpha * 100.0)


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
    return match is not None and match.group(1) in CSS_FUNCTION_NAMES


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

        Percentages are accepted wherever CSS Color 4 gives the component a
        reference, and scale against that function's own reference rather than
        a shared one: ``100%`` is 125 for ``lab()``'s a and b, 150 for
        ``lch()``'s chroma, and 0.4 for both of the Oklab pair. ``100%`` is the
        reference and not a maximum, so a larger percentage parses and is then
        refused by the range check, exactly as the equivalent number is.

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
    >>> css2hsla("oklch(0.6 25% 200)") == css2hsla("oklch(0.6 0.1 200)")
    True
    """
    text = css.strip().lower()
    if text == "transparent":
        return HSLA(0.0, 0.0, 0.0, 0.0)

    match = CSS_FUNCTION.fullmatch(text)
    if match is None or match.group(1) not in CSS_FUNCTION_NAMES:
        raise InvalidColorError(f"Not a CSS color function: {css!r}.")
    name, arguments = match.group(1), match.group(2)
    if name == "color":
        ## A keyword and three components rather than three components, so it
        ## does not fit the table the others are read from.
        tokens, alpha_token = _split_arguments(arguments)
        alpha = 1.0 if alpha_token is None else _read_alpha(alpha_token)
        if not 0.0 <= alpha <= 1.0:
            raise InvalidColorError(f"Alpha must be between 0 and 1, not {alpha}.")
        return _predefined_color(tokens, alpha)
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
