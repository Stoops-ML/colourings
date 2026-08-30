import re
from collections.abc import Callable, Hashable, Sequence
from functools import lru_cache, wraps
from typing import ParamSpec, TypeVar

from .definitions import (
    COLOR_NAME_TO_RGB,
    FLOAT_ERROR,
    HSL,
    HSLA,
    LONG_HEX_COLOR,
    RGB,
    RGB_TO_COLOR_NAMES,
    RGBA,
    SHORT_HEX_COLOR,
    HSLAf,
    HSLf,
    RGBAf,
    RGBf,
)
from .errors import ColorError, InvalidColorError
from .identify import (
    is_hsl,
    is_hsla,
    is_hslf,
    is_long_hex,
    is_rgb,
    is_rgba,
    is_rgbaf,
    is_rgbf,
    is_short_hex,
    is_web,
)

# add HSV, CMYK, YUV conversion

P = ParamSpec("P")
R = TypeVar("R")

## Conversions are pure functions of their arguments and return immutable
## values, so results can be memoised and shared between callers. The cache is
## bounded because hex and RGB inputs form a very large key space, while the
## palette an application actually uses is typically tiny.
CACHE_SIZE = 1024

_caches: list[Callable[[], None]] = []


def _hashable(value: object) -> Hashable:
    """Return a hashable equivalent of a conversion argument.

    Parameters
    ----------
    value : object
        Argument passed to a conversion helper.

    Returns
    -------
    Hashable
        ``value`` as a tuple when it is a non-string sequence, otherwise
        ``value`` unchanged.

    Raises
    ------
    TypeError
        Raised when ``value`` cannot be used as a cache key.
    """
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    if isinstance(value, Hashable):
        return value
    raise TypeError(f"Unhashable argument of type {type(value).__name__}.")


def _cached(func: Callable[P, R]) -> Callable[P, R]:
    """Memoize a conversion, normalizing sequence arguments to hashable tuples.

    The conversion helpers accept any ``Sequence``, including lists, which
    ``lru_cache`` cannot use as a key. Sequence arguments are converted to
    tuples before reaching the cache, so passing a list behaves exactly as it
    did before, and a list and the equivalent tuple share a cache entry.

    Parameters
    ----------
    func : Callable[P, R]
        Pure conversion function to memoize.

    Returns
    -------
    Callable[P, R]
        Wrapper with the same signature, backed by a bounded LRU cache.
    """
    cached = lru_cache(maxsize=CACHE_SIZE)(func)
    _caches.append(cached.cache_clear)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if not kwargs:
            try:
                ## Tuples and strings, which is what conversions are normally
                ## given, key the cache directly and skip the work below.
                return cached(*args)
            except ColorError:
                ## A rejected colour, not an unhashable argument. Re-raise it
                ## rather than falling through and running the conversion twice.
                raise
            except TypeError:
                pass
        try:
            key_args = tuple(_hashable(a) for a in args)
            key_kwargs = {k: _hashable(v) for k, v in kwargs.items()}
        except TypeError:
            ## An argument that cannot be a cache key at all is passed straight
            ## through, so the conversion still raises its own error rather than
            ## one from the cache.
            return func(*args, **kwargs)
        return cached(*key_args, **key_kwargs)

    return wrapper


def clear_caches() -> None:
    """Empty every conversion cache.

    Conversions are pure, so this is never needed for correctness. It is
    provided to release the memory held by cached results.

    Returns
    -------
    None
        This function clears the caches in place.
    """
    for cache_clear in _caches:
        cache_clear()


def _threshold(value: float) -> float:
    """Clamp tiny floating-point noise to zero.

    Parameters
    ----------
    value : float
        Floating-point value to normalize.

    Returns
    -------
    float
        ``0.0`` when ``abs(value) < FLOAT_ERROR``; otherwise ``value`` as float.
    """
    if abs(value) < FLOAT_ERROR:
        return 0.0
    return float(value)


@_cached
def rgbf2rgb(rgbf: Sequence[int | float]) -> RGB:
    """Convert normalized RGB components into 0-255 RGB components.

    Parameters
    ----------
    rgbf : Sequence[int | float]
        RGB sequence in the ``[0, 1]`` range.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    return RGB(
        _threshold(rgbf[0] * 255.0),
        _threshold(rgbf[1] * 255.0),
        _threshold(rgbf[2] * 255.0),
    )


@_cached
def rgb2rgba(rgb: Sequence[int | float], alpha: int | float) -> RGBA:
    """Build an RGBA tuple from RGB values and normalized alpha.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.
    alpha : int | float
        Alpha channel in the ``[0, 1]`` range.

    Returns
    -------
    RGBA
        RGBA tuple with alpha scaled to ``[0, 255]``.
    """
    return RGBA(
        _threshold(rgb[0]),
        _threshold(rgb[1]),
        _threshold(rgb[2]),
        _threshold(alpha * 255.0),
    )


@_cached
def rgb2rgbf(rgb: Sequence[int | float]) -> RGBf:
    """Convert 0-255 RGB components into normalized RGB components.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    RGBf
        RGB tuple in the ``[0, 1]`` range.
    """
    return RGBf(
        _threshold(rgb[0] / 255.0),
        _threshold(rgb[1] / 255.0),
        _threshold(rgb[2] / 255.0),
    )


@_cached
def rgb2rgbaf(rgb: Sequence[int | float], alpha: int | float) -> RGBAf:
    """Build an RGBAf tuple from RGB values and alpha.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.
    alpha : int | float
        Alpha channel in the ``[0, 1]`` range.

    Returns
    -------
    RGBAf
        RGBAf tuple with RGB normalized to ``[0, 1]`` and alpha unchanged.
    """
    return RGBAf(
        _threshold(rgb[0] / 255.0),
        _threshold(rgb[1] / 255.0),
        _threshold(rgb[2] / 255.0),
        _threshold(alpha),
    )


@_cached
def hsl2hsla(hsl: Sequence[int | float], alpha: int | float) -> HSLA:
    """Build an HSLA tuple from HSL values and normalized alpha.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)`` with ``h`` in ``[0, 360]`` and ``s``, ``l`` in ``[0, 100]``.
    alpha : int | float
        Alpha channel in the ``[0, 1]`` range.

    Returns
    -------
    HSLA
        HSLA tuple with alpha scaled to ``[0, 100]``.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not an HSL type.")
    return HSLA(
        _threshold(hsl[0]),
        _threshold(hsl[1]),
        _threshold(hsl[2]),
        _threshold(alpha * 100),
    )


@_cached
def hsl2hslaf(hsl: Sequence[int | float], alpha: int | float) -> HSLAf:
    """Convert HSL values and alpha to normalized HSLAf representation.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)`` with ``h`` in ``[0, 360]`` and ``s``, ``l`` in ``[0, 100]``.
    alpha : int | float
        Alpha channel in the ``[0, 1]`` range.

    Returns
    -------
    HSLAf
        HSLAf tuple where hue is scaled to ``[0, 1]`` and saturation/lightness to ``[0, 1]``.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not an HSL type.")
    return HSLAf(
        _threshold(hsl[0] / 360.0),
        _threshold(hsl[1] / 100.0),
        _threshold(hsl[2] / 100.0),
        _threshold(alpha),
    )


@_cached
def hslf2hsl(hslf: Sequence[int | float]) -> HSL:
    """Convert normalized HSL components to standard HSL representation.

    Parameters
    ----------
    hslf : Sequence[int | float]
        Normalized HSL sequence in ``[0, 1]``.

    Returns
    -------
    HSL
        HSL tuple with hue in ``[0, 360]`` and saturation/lightness in ``[0, 100]``.
    """
    if not is_hslf(hslf):
        raise InvalidColorError("Input is not an HSLf type.")
    return HSL(
        _threshold(hslf[0] * 360.0),
        _threshold(hslf[1] * 100.0),
        _threshold(hslf[2] * 100.0),
    )


@_cached
def hsl2hslf(hsl: Sequence[int | float]) -> HSLf:
    """Convert standard HSL components to normalized HSLf representation.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)`` with hue in degrees and saturation/lightness in percent.

    Returns
    -------
    HSLf
        HSLf tuple normalized to ``[0, 1]``.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not an HSLf type.")
    return HSLf(
        _threshold(hsl[0] / 360.0),
        _threshold(hsl[1] / 100.0),
        _threshold(hsl[2] / 100.0),
    )


@_cached
def hsl2rgb(hsl: Sequence[int | float]) -> RGB:
    """Convert HSL representation to RGB representation.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)`` where hue is in degrees and saturation/lightness are percentages.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not an HSL type.")
    r, g, b = _hsl2rgbf(hsl)
    return RGB(
        _threshold(r * 255.0),
        _threshold(g * 255.0),
        _threshold(b * 255.0),
    )


@_cached
def hsl2rgbf(hsl: Sequence[int | float]) -> RGBf:
    """Convert HSL representation to normalized RGB representation.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    RGBf
        RGBf tuple in the ``[0, 1]`` range.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not an HSL type.")
    r, g, b = _hsl2rgbf(hsl)
    return RGBf(_threshold(r), _threshold(g), _threshold(b))


@_cached
def rgba2hsl(rgba: Sequence[int | float]) -> HSL:
    """Convert RGBA values to HSL values, ignoring alpha.

    Parameters
    ----------
    rgba : Sequence[int | float]
        RGBA sequence with RGB in ``[0, 255]`` and alpha in ``[0, 255]``.

    Returns
    -------
    HSL
        HSL tuple.
    """
    if not is_rgba(rgba):
        raise InvalidColorError("Input is not an RGBA type.")
    return rgb2hsl(rgba[:3])


@_cached
def rgbaf2hsl(rgbaf: Sequence[int | float]) -> HSL:
    """Convert RGBAf values to HSL values, ignoring alpha.

    Parameters
    ----------
    rgbaf : Sequence[int | float]
        RGBAf sequence with RGB and alpha in ``[0, 1]``.

    Returns
    -------
    HSL
        HSL tuple.
    """
    if not is_rgbaf(rgbaf):
        raise InvalidColorError("Input is not an RGBAf type.")
    return _rgbf2hsl(_threshold(rgbaf[0]), _threshold(rgbaf[1]), _threshold(rgbaf[2]))


@_cached
def hsla2hsl(hsla: Sequence[int | float]) -> HSL:
    """Convert HSLA values to HSL values, ignoring alpha.

    Parameters
    ----------
    hsla : Sequence[int | float]
        HSLA sequence with hue in degrees, saturation/lightness in percent, and alpha in percent.

    Returns
    -------
    HSL
        HSL tuple.
    """
    if not is_hsla(hsla):
        raise InvalidColorError("Input is not an HSLA type.")
    return HSL(_threshold(hsla[0]), _threshold(hsla[1]), _threshold(hsla[2]))


@_cached
def rgbf2hsl(rgbf: Sequence[int | float]) -> HSL:
    """Convert normalized RGB values to HSL values.

    Parameters
    ----------
    rgbf : Sequence[int | float]
        RGBf sequence in ``[0, 1]``.

    Returns
    -------
    HSL
        HSL tuple.
    """
    if not is_rgbf(rgbf):
        raise InvalidColorError("Input is not an RGBf type.")
    return _rgbf2hsl(_threshold(rgbf[0]), _threshold(rgbf[1]), _threshold(rgbf[2]))


@_cached
def rgb2hsl(rgb: Sequence[int | float]) -> HSL:
    """Convert RGB representation to HSL representation.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    HSL
        HSL tuple where hue is in ``[0, 360]`` and saturation/lightness are in ``[0, 100]``.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    return _rgbf2hsl(*rgb2rgbf(rgb))


def _rgbf2hsl(r: float, g: float, b: float) -> HSL:
    """Convert already normalized RGB components to HSL.

    Shared by every RGB-to-HSL entry point so that components which are
    already in the ``[0, 1]`` range are not scaled up to ``[0, 255]`` and
    immediately back down.

    Parameters
    ----------
    r : float
        Red component in the ``[0, 1]`` range.
    g : float
        Green component in the ``[0, 1]`` range.
    b : float
        Blue component in the ``[0, 1]`` range.

    Returns
    -------
    HSL
        HSL tuple where hue is in ``[0, 360]`` and saturation/lightness are in ``[0, 100]``.
    """
    vmin = min(r, g, b)  ## Min. value of RGB
    vmax = max(r, g, b)  ## Max. value of RGB
    diff = vmax - vmin  ## Delta RGB value

    vsum = vmin + vmax

    _l = vsum / 2

    if diff < FLOAT_ERROR:  ## This is a gray, no chroma...
        return HSL(0.0, 0.0, _threshold(_l * 100.0))

    ##
    ## Chromatic data...
    ##

    ## Saturation
    s = diff / vsum if _l < 0.5 else diff / (2.0 - vsum)

    dr = (((vmax - r) / 6) + (diff / 2)) / diff
    dg = (((vmax - g) / 6) + (diff / 2)) / diff
    db = (((vmax - b) / 6) + (diff / 2)) / diff

    if r == vmax:
        h = db - dg
    elif g == vmax:
        h = (1.0 / 3) + dr - db
    else:  ## b == vmax
        h = (2.0 / 3) + dg - dr

    if h < 0:
        h += 1
    if h > 1:
        h -= 1

    return HSL(
        _threshold(h * 360.0),
        _threshold(s * 100.0),
        _threshold(_l * 100.0),
    )


def _hsl2rgbf(hsl: Sequence[int | float]) -> tuple[float, float, float]:
    """Convert HSL to normalized RGB components.

    Shared by ``hsl2rgb`` and ``hsl2rgbf`` so that the normalized components
    this produces are not scaled up to ``[0, 255]`` and immediately back down.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)`` with hue in degrees and saturation/lightness in percent.

    Returns
    -------
    tuple[float, float, float]
        RGB components in the ``[0, 1]`` range.
    """
    _h, _s, _l = (float(v) for v in hsl)
    _h /= 360.0
    _s /= 100.0
    _l /= 100.0

    if _s == 0:  ## This is a gray, no chroma...
        return (_l, _l, _l)

    v2 = _l * (1.0 + _s) if _l < 0.5 else (_l + _s) - (_s * _l)

    v1 = 2.0 * _l - v2

    return (
        _hue2rgb(v1, v2, _h + (1.0 / 3)),
        _hue2rgb(v1, v2, _h),
        _hue2rgb(v1, v2, _h - (1.0 / 3)),
    )


def _hue2rgb(v1: float, v2: float, vH: float) -> float:
    """Interpolate a single RGB channel from hue data.

    Parameters
    ----------
    v1 : float
        Lower interpolation bound.
    v2 : float
        Upper interpolation bound.
    vH : float
        Hue phase in normalized turns.

    Returns
    -------
    float
        Interpolated channel value in ``[0, 1]``.
    """

    while vH < 0:
        vH += 1
    while vH > 1:
        vH -= 1

    if 6 * vH < 1:
        return v1 + (v2 - v1) * 6 * vH
    if 2 * vH < 1:
        return v2
    if 3 * vH < 2:
        return v1 + (v2 - v1) * ((2.0 / 3) - vH) * 6

    return v1


@_cached
def rgb2hex(rgb: Sequence[int | float], force_long: bool = False) -> str:
    """Convert RGB components to a hexadecimal color string.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.
    force_long : bool, default=False
        Whether to force 6-digit output even when shorthand form is possible.

    Returns
    -------
    str
        Hex color string prefixed with ``#``.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not of RGB type.")

    hx = "".join([f"{int(c + 0.5 - FLOAT_ERROR):02x}" for c in rgb])

    if not force_long and hx[0::2] == hx[1::2]:
        hx = "".join(hx[0::2])

    return f"#{hx}"


@_cached
def hex2rgb(hex: str) -> RGB:
    """Convert a hexadecimal color string to RGB components.

    Parameters
    ----------
    hex : str
        3-digit or 6-digit hexadecimal color string prefixed with ``#``.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """

    if not (is_long_hex(hex) or is_short_hex(hex)):
        raise InvalidColorError("Input is not of hex type.")

    try:
        rgb = hex[1:]

        if len(rgb) == 6:
            r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
        elif len(rgb) == 3:
            r, g, b = rgb[0] * 2, rgb[1] * 2, rgb[2] * 2
        else:
            raise InvalidColorError("Length of rgb must be either three or six.")
    except Exception as e:
        raise InvalidColorError(f"Invalid value {hex} provided for rgb color.") from e

    return RGB(
        _threshold(float(int(r, 16))),
        _threshold(float(int(g, 16))),
        _threshold(float(int(b, 16))),
    )


@_cached
def hex2web(hex: str) -> str:
    """Convert a hexadecimal color to a web representation.

    Parameters
    ----------
    hex : str
        3-digit or 6-digit hexadecimal color string prefixed with ``#``.

    Returns
    -------
    str
        Named CSS color when available, otherwise a hex string (possibly shortened).
    """
    if not (is_long_hex(hex) or is_short_hex(hex)):
        raise InvalidColorError("Input is not of hex type.")

    rgb = hex2rgb(hex)
    ## Table keys are whole numbers, so truncate before looking the color up.
    dec_rgb = RGB(float(int(rgb[0])), float(int(rgb[1])), float(int(rgb[2])))
    if dec_rgb in RGB_TO_COLOR_NAMES:
        ## take the first one
        color_name = RGB_TO_COLOR_NAMES[dec_rgb][0]
        ## Enforce full lowercase for single worded color name.
        return (
            color_name
            if len(re.sub(r"[^A-Z]", "", color_name)) > 1
            else color_name.lower()
        )

    # Hex format is verified by hex2rgb function. And should be 3 or 6 digit
    if len(hex) == 7 and hex[1] == hex[2] and hex[3] == hex[4] and hex[5] == hex[6]:
        return "#" + hex[1] + hex[3] + hex[5]
    return hex


@_cached
def web2hex(web: str, force_long: bool = False) -> str:
    """Convert a web color representation to hexadecimal form.

    Parameters
    ----------
    web : str
        CSS color name or hexadecimal color string.
    force_long : bool, default=False
        Whether to force 6-digit output for shorthand hex inputs.

    Returns
    -------
    str
        Hex color string prefixed with ``#``.
    """
    web = web.lower()
    if web.startswith("#"):
        if LONG_HEX_COLOR.match(web) or (not force_long and SHORT_HEX_COLOR.match(web)):
            return web.lower()
        elif SHORT_HEX_COLOR.match(web) and force_long:
            return "#" + "".join([str(t) * 2 for t in web[1:]])
        raise InvalidColorError(f"{web} is not in web format. Need 3 or 6 hex digit.")

    if not is_web(web):
        raise InvalidColorError("Input is not of web type.")
    return rgb2hex(COLOR_NAME_TO_RGB[web], force_long)  # convert dec to hex


@_cached
def hsl2hex(hsl: Sequence[int | float]) -> str:
    """Convert HSL values to a hexadecimal color string.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    str
        Hex color string.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not of hsl type.")
    return rgb2hex(hsl2rgb(hsl))


@_cached
def hex2hsl(hex: str) -> HSL:
    """Convert a hexadecimal color string to HSL values.

    Parameters
    ----------
    hex : str
        3-digit or 6-digit hexadecimal color string.

    Returns
    -------
    HSL
        HSL tuple.
    """
    if not (is_long_hex(hex) or is_short_hex(hex)):
        raise InvalidColorError("Input is not of hex type.")
    return rgb2hsl(hex2rgb(hex))


@_cached
def rgb2web(rgb: Sequence[int | float]) -> str:
    """Convert RGB values to a web color representation.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    str
        Named CSS color when available, otherwise hex.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    return hex2web(rgb2hex(rgb))


@_cached
def web2rgb(web: str) -> RGB:
    """Convert a web color representation to RGB values.

    Parameters
    ----------
    web : str
        CSS color name or hex color string.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    if not is_web(web):
        raise InvalidColorError("Input is not of web type.")
    return hex2rgb(web2hex(web))


@_cached
def web2hsl(web: str) -> HSL:
    """Convert a web color representation to HSL values.

    Parameters
    ----------
    web : str
        CSS color name or hex color string.

    Returns
    -------
    HSL
        HSL tuple.
    """
    if not is_web(web):
        raise InvalidColorError("Input is not an web type.")
    return rgb2hsl(web2rgb(web))


@_cached
def hsl2web(hsl: Sequence[int | float]) -> str:
    """Convert HSL values to a web color representation.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    str
        Named CSS color when available, otherwise hex.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not an HSL type.")
    return rgb2web(hsl2rgb(hsl))
