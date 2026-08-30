from collections.abc import Sequence

from .definitions import COLOR_NAME_TO_RGB, LONG_HEX_COLOR, SHORT_HEX_COLOR


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
        component in the ``[0, 255]`` range.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 3:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 255):
            return False
    return True


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
        component in the ``[0, 1]`` range.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 3:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 1):
            return False
    return True


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
        component in the ``[0, 1]`` range.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 3:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 1):
            return False
    return True


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
        component in the ``[0, 255]`` range.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 4:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 255):
            return False
    return True


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
        component in the ``[0, 1]`` range.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 4:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 1):
            return False
    return True


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
        component in the ``[0, 1]`` range.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 4:
        return False
    for channel in color:
        if not isinstance(channel, int | float) or not (0 <= channel <= 1):
            return False
    return True


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
        ``[0, 360]`` and saturation/lightness in ``[0, 100]``.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 3:
        return False
    if isinstance(color[0], int | float) and not 0 <= color[0] <= 360:
        return False
    for channel in color[1:]:
        if not isinstance(channel, int | float) or not (0 <= channel <= 100):
            return False
    return True


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
        ``[0, 360]`` and saturation/lightness/alpha in ``[0, 100]``.
    """
    if not isinstance(color, Sequence) or isinstance(color, str):
        return False
    if len(color) != 4:
        return False
    if isinstance(color[0], int | float) and not 0 <= color[0] <= 360:
        return False
    for channel in color[1:]:
        if not isinstance(channel, int | float) or not (0 <= channel <= 100):
            return False
    return True
