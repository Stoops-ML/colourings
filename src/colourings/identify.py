from collections.abc import Sequence

from .definitions import (
    COLOR_NAME_TO_RGB,
    FLOAT_ERROR,
    LONG_HEX_ALPHA_COLOR,
    LONG_HEX_COLOR,
    SHORT_HEX_ALPHA_COLOR,
    SHORT_HEX_COLOR,
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


def _is_color(color: object, length: int, low: float, high: float) -> bool:
    """Check whether a value is a colour sequence with components in range.

    Parameters
    ----------
    color : object
        Candidate value.
    length : int
        Number of components the sequence must have.
    low : float
        Lower bound each component must satisfy.
    high : float
        Upper bound each component must satisfy.

    Returns
    -------
    bool
        True when ``color`` is a non-string sequence of ``length`` numbers,
        each within ``FLOAT_ERROR`` of ``[low, high]``.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != length:
        return False
    return all(_in_range(channel, low, high) for channel in color)


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
    return _is_color(color, 3, 0, 255)


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
    return _is_color(color, 3, 0, 1)


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
    return _is_color(color, 3, 0, 1)


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
    return _is_color(color, 4, 0, 255)


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
    return _is_color(color, 4, 0, 1)


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
    return _is_color(color, 4, 0, 1)


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
    return _is_color_ranges(color, ((0, 360), (0, 100), (0, 100)))


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
    return _is_color_ranges(color, ((0, 360), (0, 100), (0, 100)))


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
    return _is_color_ranges(color, ((0, 360), (0, 100), (0, 100), (0, 100)))


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
    return _is_color_ranges(color, ((0, 110), (0, 110), (0, 110)))


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
    return _is_color_ranges(color, ((0, 100), (-128, 127), (-128, 127)))


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
    return _is_color_ranges(color, ((0, 100), (0, 182), (0, 360)))


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
    return _is_color_ranges(color, ((0, 1), (-0.4, 0.4), (-0.4, 0.4)))


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
    return _is_color_ranges(color, ((0, 1), (0, 0.4), (0, 360)))


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
    return _is_color(color, 4, 0, 100)


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
    return _is_color_ranges(color, ((0, 1), (-0.436, 0.436), (-0.615, 0.615)))
