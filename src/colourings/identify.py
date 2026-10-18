from __future__ import annotations

from collections.abc import Sequence

from .definitions import (
    CMYK,
    COLOR_NAME_TO_RGB,
    FLOAT_ERROR,
    HSL,
    HSLA,
    HSV,
    LAB,
    LCH,
    LONG_HEX_ALPHA_COLOR,
    LONG_HEX_COLOR,
    OKLAB,
    OKLCH,
    RGB,
    RGBA,
    SHORT_HEX_ALPHA_COLOR,
    SHORT_HEX_COLOR,
    XYZ,
    YUV,
    HSLAf,
    HSLf,
    RGBAf,
    RGBf,
)


def _in_range(value: object, low: float, high: float) -> bool:
    """Check whether a value is a number inside an inclusive range.

    The bounds are widened by ``FLOAT_ERROR`` because the conversion helpers
    can land a hair outside the range they are documented to produce. For
    example ``rgb2hsl((245, 255, 250))``, the RGB behind ``mintcream``,
    returns a saturation of ``100.00000000000028``.

    Parameters
    ----------
    value : object
        Candidate component.
    low : float
        Lower bound of the range.
    high : float
        Upper bound of the range.

    Returns
    -------
    bool
        True when ``value`` is a number within ``FLOAT_ERROR`` of the range.
    """
    if not isinstance(value, int | float):
        return False
    return low - FLOAT_ERROR <= value <= high + FLOAT_ERROR


def _is_color_ranges(color: object, ranges: Sequence[tuple[float, float]]) -> bool:
    """Check a colour sequence whose components have different ranges.

    Parameters
    ----------
    color : object
        Candidate value.
    ranges : Sequence[tuple[float, float]]
        One ``(low, high)`` pair per component, in order.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of the same length as
        ``ranges`` and each component lies within its own range.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != len(ranges):
        return False
    return all(
        _in_range(channel, low, high)
        for channel, (low, high) in zip(color, ranges, strict=True)
    )


_UNIT = (0, 1)
_BYTE = (0, 255)
_HUE = (0, 360)
_PERCENT = (0, 100)

## One table, so a validator and the message explaining its refusal agree.
_RANGES: dict[str, tuple[tuple[float, float], ...]] = {
    "rgb": (_BYTE,) * 3,
    "rgba": (_BYTE,) * 4,
    "rgbf": (_UNIT,) * 3,
    "rgbaf": (_UNIT,) * 4,
    "hsl": (_HUE, _PERCENT, _PERCENT),
    "hsla": (_HUE, _PERCENT, _PERCENT, _PERCENT),
    "hslf": (_UNIT,) * 3,
    "hslaf": (_UNIT,) * 4,
    "hsv": (_HUE, _PERCENT, _PERCENT),
    "xyz": ((0, 110),) * 3,
    "lab": (_PERCENT, (-128, 127), (-128, 127)),
    "lch": (_PERCENT, (0, 182), _HUE),
    "oklab": (_UNIT, (-0.4, 0.4), (-0.4, 0.4)),
    "oklch": (_UNIT, (0, 0.4), _HUE),
    "cmyk": (_PERCENT,) * 4,
    "yuv": (_UNIT, (-0.436, 0.436), (-0.615, 0.615)),
}

_COMPONENTS: dict[str, tuple[str, ...]] = {
    "rgb": RGB._fields,
    "rgba": RGBA._fields,
    "rgbf": RGBf._fields,
    "rgbaf": RGBAf._fields,
    "hsl": HSL._fields,
    "hsla": HSLA._fields,
    "hslf": HSLf._fields,
    "hslaf": HSLAf._fields,
    "hsv": HSV._fields,
    "xyz": XYZ._fields,
    "lab": LAB._fields,
    "lch": LCH._fields,
    "oklab": OKLAB._fields,
    "oklch": OKLCH._fields,
    "cmyk": CMYK._fields,
    "yuv": YUV._fields,
}


def why_invalid(form: str, color: object) -> str:
    """Say which part of a sequence its format's validator rejected.

    Parameters
    ----------
    form : str
        The format, as a key of the range table, such as ``"rgb"``.
    color : object
        The value that failed validation.

    Returns
    -------
    str
        A sentence to append to a message, beginning with a space, or ``""``
        when ``color`` is in fact valid.

    Examples
    --------
    >>> why_invalid("rgb", (300, 0, 0))
    ' red=300 is outside [0, 255].'
    >>> why_invalid("hsl", (0, 50))
    ' hsl takes 3 components (hue, saturation, lightness), not 2.'
    """
    ranges = _RANGES[form]
    names = _COMPONENTS[form]
    if not isinstance(color, Sequence) or isinstance(color, str):
        return f" {form} takes a sequence of {len(ranges)} numbers, not {type(color).__name__}."
    if len(color) != len(ranges):
        return (
            f" {form} takes {len(ranges)} components ({', '.join(names)}), "
            f"not {len(color)}."
        )
    for name, channel, (low, high) in zip(names, color, ranges, strict=True):
        if not isinstance(channel, int | float):
            return f" {name}={channel!r} is not a number."
        if not _in_range(channel, low, high):
            return f" {name}={channel:g} is outside [{low}, {high}]."
    return ""


def is_long_hex(color: str) -> bool:
    """Check whether a string is a 6-digit hexadecimal color.

    Parameters
    ----------
    color : str
        Candidate color string.

    Returns
    -------
    bool
        True if the value matches a long hex format like ``#aabbcc``.
    """
    return bool(LONG_HEX_COLOR.fullmatch(color))


def is_short_hex(color: str) -> bool:
    """Check whether a string is a 3-digit hexadecimal color.

    Parameters
    ----------
    color : str
        Candidate color string.

    Returns
    -------
    bool
        True if the value matches a short hex format like ``#abc``.
    """
    return bool(SHORT_HEX_COLOR.fullmatch(color))


def is_long_hex_alpha(color: str) -> bool:
    """Check whether a string is an 8-digit hexadecimal color with alpha.

    Parameters
    ----------
    color : str
        Candidate color string.

    Returns
    -------
    bool
        True if the value matches a long hex-with-alpha form like ``#aabbccdd``.
    """
    return bool(LONG_HEX_ALPHA_COLOR.fullmatch(color))


def is_short_hex_alpha(color: str) -> bool:
    """Check whether a string is a 4-digit hexadecimal color with alpha.

    Parameters
    ----------
    color : str
        Candidate color string.

    Returns
    -------
    bool
        True if the value matches a short hex-with-alpha form like ``#abcd``.
    """
    return bool(SHORT_HEX_ALPHA_COLOR.fullmatch(color))


def is_hex_alpha(color: str) -> bool:
    """Check whether a string is a hexadecimal color that carries an alpha.

    Parameters
    ----------
    color : str
        Candidate color string.

    Returns
    -------
    bool
        True for either the 4-digit or the 8-digit form.
    """
    return is_long_hex_alpha(color) or is_short_hex_alpha(color)


def is_rgb(color: object) -> bool:
    """Validate whether a value is an RGB sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with each
        component in the ``[0, 255]`` range, within ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["rgb"])


def is_rgbf(color: object) -> bool:
    """Validate whether a value is a normalized RGB sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with each
        component in the ``[0, 1]`` range, within ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["rgbf"])


def is_hslf(color: object) -> bool:
    """Validate whether a value is a normalized HSL sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with each
        component in the ``[0, 1]`` range, within ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["hslf"])


def is_rgba(color: object) -> bool:
    """Validate whether a value is an RGBA sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 4 with each
        component in the ``[0, 255]`` range, within ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["rgba"])


def is_rgbaf(color: object) -> bool:
    """Validate whether a value is a normalized RGBA sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 4 with each
        component in the ``[0, 1]`` range, within ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["rgbaf"])


def is_hslaf(color: object) -> bool:
    """Validate whether a value is a normalized HSLA sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 4 with each
        component in the ``[0, 1]`` range, within ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["hslaf"])


def is_web(color: str) -> bool:
    """Check whether a string is a valid web color representation.

    Parameters
    ----------
    color : str
        Candidate color string.

    Returns
    -------
    bool
        True when ``color`` is a known color name or a valid short/long hex.
    """
    return color in COLOR_NAME_TO_RGB or is_long_hex(color) or is_short_hex(color)


def is_hsl(color: object) -> bool:
    """Validate whether a value is an HSL sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with hue in
        ``[0, 360]`` and saturation/lightness in ``[0, 100]``, each within
        ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["hsl"])


def is_hsv(color: object) -> bool:
    """Validate whether a value is an HSV sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with hue in
        ``[0, 360]`` and saturation/value in ``[0, 100]``, each within
        ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["hsv"])


def is_hsla(color: object) -> bool:
    """Validate whether a value is an HSLA sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 4 with hue in
        ``[0, 360]`` and saturation/lightness/alpha in ``[0, 100]``, each
        within ``FLOAT_ERROR``.
    """
    return _is_color_ranges(color, _RANGES["hsla"])


def is_xyz(color: object) -> bool:
    """Validate whether a value is a CIE XYZ sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 whose
        components lie within the bounds the sRGB gamut occupies under D65.
    """
    return _is_color_ranges(color, _RANGES["xyz"])


def is_lab(color: object) -> bool:
    """Validate whether a value is a CIE L*a*b* sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with lightness
        in ``[0, 100]`` and a/b in ``[-128, 127]``.
    """
    return _is_color_ranges(color, _RANGES["lab"])


def is_lch(color: object) -> bool:
    """Validate whether a value is a CIE LCh sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with lightness
        in ``[0, 100]``, chroma in ``[0, 182]`` and hue in ``[0, 360]``.
    """
    return _is_color_ranges(color, _RANGES["lch"])


def is_oklab(color: object) -> bool:
    """Validate whether a value is an Oklab sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with lightness
        in ``[0, 1]`` and a/b in ``[-0.4, 0.4]``.
    """
    return _is_color_ranges(color, _RANGES["oklab"])


def is_oklch(color: object) -> bool:
    """Validate whether a value is an Oklch sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with lightness
        in ``[0, 1]``, chroma in ``[0, 0.4]`` and hue in ``[0, 360]``.
    """
    return _is_color_ranges(color, _RANGES["oklch"])


def is_cmyk(color: object) -> bool:
    """Validate whether a value is a CMYK sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 4 with each
        component in the ``[0, 100]`` range.
    """
    return _is_color_ranges(color, _RANGES["cmyk"])


def is_yuv(color: object) -> bool:
    """Validate whether a value is a BT.601 YUV sequence.

    Parameters
    ----------
    color : object
        Candidate value.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of length 3 with luma in
        ``[0, 1]``, U in ``[-0.436, 0.436]`` and V in ``[-0.615, 0.615]``.
    """
    return _is_color_ranges(color, _RANGES["yuv"])
