import math
import re
from collections.abc import Callable, Hashable, Sequence
from functools import lru_cache, wraps
from typing import ParamSpec, TypeVar

from .definitions import (
    CMYK,
    COLOR_NAME_TO_RGB,
    D65_WHITE_POINT,
    FLOAT_ERROR,
    HSL,
    HSLA,
    HSV,
    LAB,
    LAB_DELTA,
    LCH,
    LMS_TO_OKLAB_MATRIX,
    LMS_TO_RGB_MATRIX,
    LONG_HEX_COLOR,
    OKLAB,
    OKLAB_TO_LMS_MATRIX,
    OKLCH,
    RGB,
    RGB_TO_COLOR_NAMES,
    RGB_TO_LMS_MATRIX,
    RGB_TO_XYZ_MATRIX,
    RGBA,
    SHORT_HEX_COLOR,
    WCAG_CONTRAST_FLARE,
    WCAG_LUMINANCE_COEFFICIENTS,
    XYZ,
    XYZ_TO_RGB_MATRIX,
    YUV,
    YUV_LUMA_COEFFICIENTS,
    YUV_U_SCALE,
    YUV_V_SCALE,
    HSLAf,
    HSLf,
    RGBAf,
    RGBf,
)
from .errors import ColorError, InvalidColorError
from .identify import (
    is_cmyk,
    is_hsl,
    is_hsla,
    is_hslf,
    is_hsv,
    is_lab,
    is_lch,
    is_long_hex,
    is_oklab,
    is_oklch,
    is_rgb,
    is_rgba,
    is_rgbaf,
    is_rgbf,
    is_short_hex,
    is_web,
    is_xyz,
    is_yuv,
)

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


@_cached
def hsl2hsv(hsl: Sequence[int | float]) -> HSV:
    """Convert HSL representation to HSV representation.

    Both models share a hue; only the saturation and the third component
    differ, so the conversion is exact rather than a round trip through RGB.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)`` with hue in degrees and
        saturation/lightness in percent.

    Returns
    -------
    HSV
        HSV tuple where hue is in ``[0, 360]`` and saturation/value are in
        ``[0, 100]``.
    """
    if not is_hsl(hsl):
        raise InvalidColorError("Input is not an HSL type.")
    _h, _s, _l = (float(v) for v in hsl)
    _s /= 100.0
    _l /= 100.0

    value = _l + _s * min(_l, 1.0 - _l)
    saturation = 0.0 if value == 0 else 2.0 * (1.0 - _l / value)

    return HSV(
        _threshold(_h),
        _threshold(saturation * 100.0),
        _threshold(value * 100.0),
    )


@_cached
def hsv2hsl(hsv: Sequence[int | float]) -> HSL:
    """Convert HSV representation to HSL representation.

    Parameters
    ----------
    hsv : Sequence[int | float]
        HSV sequence as ``(h, s, v)`` with hue in degrees and saturation/value
        in percent.

    Returns
    -------
    HSL
        HSL tuple where hue is in ``[0, 360]`` and saturation/lightness are in
        ``[0, 100]``.
    """
    if not is_hsv(hsv):
        raise InvalidColorError("Input is not an HSV type.")
    _h, _s, _v = (float(v) for v in hsv)
    _s /= 100.0
    _v /= 100.0

    lightness = _v * (1.0 - _s / 2.0)
    denominator = min(lightness, 1.0 - lightness)
    saturation = 0.0 if denominator == 0 else (_v - lightness) / denominator

    return HSL(
        _threshold(_h),
        _threshold(saturation * 100.0),
        _threshold(lightness * 100.0),
    )


@_cached
def rgb2hsv(rgb: Sequence[int | float]) -> HSV:
    """Convert RGB representation to HSV representation.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    HSV
        HSV tuple.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    return hsl2hsv(rgb2hsl(rgb))


@_cached
def hsv2rgb(hsv: Sequence[int | float]) -> RGB:
    """Convert HSV representation to RGB representation.

    Parameters
    ----------
    hsv : Sequence[int | float]
        HSV sequence as ``(h, s, v)``.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    if not is_hsv(hsv):
        raise InvalidColorError("Input is not an HSV type.")
    return hsl2rgb(hsv2hsl(hsv))


@_cached
def hsv2hex(hsv: Sequence[int | float]) -> str:
    """Convert HSV values to a hexadecimal color string.

    Parameters
    ----------
    hsv : Sequence[int | float]
        HSV sequence as ``(h, s, v)``.

    Returns
    -------
    str
        Hex color string.
    """
    if not is_hsv(hsv):
        raise InvalidColorError("Input is not an HSV type.")
    return rgb2hex(hsv2rgb(hsv))


@_cached
def hex2hsv(hex: str) -> HSV:
    """Convert a hexadecimal color string to HSV values.

    Parameters
    ----------
    hex : str
        3-digit or 6-digit hexadecimal color string.

    Returns
    -------
    HSV
        HSV tuple.
    """
    if not (is_long_hex(hex) or is_short_hex(hex)):
        raise InvalidColorError("Input is not of hex type.")
    return hsl2hsv(hex2hsl(hex))


@_cached
def hsv2web(hsv: Sequence[int | float]) -> str:
    """Convert HSV values to a web color representation.

    Parameters
    ----------
    hsv : Sequence[int | float]
        HSV sequence as ``(h, s, v)``.

    Returns
    -------
    str
        Named CSS color when available, otherwise hex.
    """
    if not is_hsv(hsv):
        raise InvalidColorError("Input is not an HSV type.")
    return rgb2web(hsv2rgb(hsv))


@_cached
def web2hsv(web: str) -> HSV:
    """Convert a web color representation to HSV values.

    Parameters
    ----------
    web : str
        CSS color name or hex color string.

    Returns
    -------
    HSV
        HSV tuple.
    """
    if not is_web(web):
        raise InvalidColorError("Input is not of web type.")
    return hsl2hsv(web2hsl(web))


def _matrix_apply(
    matrix: Sequence[Sequence[float]], vector: Sequence[float]
) -> tuple[float, float, float]:
    """Multiply a 3x3 matrix by a 3-component vector.

    Parameters
    ----------
    matrix : Sequence[Sequence[float]]
        Three rows of three coefficients.
    vector : Sequence[float]
        Three components.

    Returns
    -------
    tuple[float, float, float]
        The product, as three floats.
    """
    return (
        matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],
        matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],
        matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2],
    )


def _srgb_to_linear(channel: float) -> float:
    """Undo the sRGB transfer function for one normalised channel.

    The results are wrapped in ``float`` because ``**`` is typed as possibly
    returning ``complex``; every base here is non-negative.

    Parameters
    ----------
    channel : float
        Gamma-encoded channel in the ``[0, 1]`` range.

    Returns
    -------
    float
        Linear-light channel in the ``[0, 1]`` range.
    """
    if channel <= 0.04045:
        return channel / 12.92
    return float(((channel + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(channel: float) -> float:
    """Apply the sRGB transfer function to one linear channel.

    Out-of-gamut values are clamped, because a colour outside sRGB has no
    representable encoding.

    Parameters
    ----------
    channel : float
        Linear-light channel.

    Returns
    -------
    float
        Gamma-encoded channel in the ``[0, 1]`` range.
    """
    channel = min(max(channel, 0.0), 1.0)
    if channel <= 0.0031308:
        return channel * 12.92
    return float(1.055 * channel ** (1 / 2.4) - 0.055)


@_cached
def rgb2relative_luminance(rgb: Sequence[int | float]) -> float:
    """Compute the WCAG 2.x relative luminance of an RGB color.

    This is luminance in the colorimetric sense: the channels are linearised
    before being weighted, so the result is proportional to the light the
    color emits. It is what a contrast ratio is built from, and it is not what
    :attr:`~colourings.colour.Color.luminance` returns.

    The standard's text gives the transfer function's breakpoint as 0.03928
    where sRGB itself gives 0.04045. This uses :func:`_srgb_to_linear`, and so
    sRGB's, both because it is the one the rest of the library applies and
    because the difference is unobservable: no 8-bit level falls between the
    two, and a float channel that does moves by at most 7.6e-07, two
    ten-thousandths of a level.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    float
        Relative luminance in ``[0, 1]``: 0 for black, 1 for white, and
        exactly the channel's coefficient for each primary.

    Raises
    ------
    InvalidColorError
        Raised when ``rgb`` is not a valid RGB value.

    Examples
    --------
    >>> rgb2relative_luminance((255, 255, 255))
    1.0
    >>> rgb2relative_luminance((255, 0, 0))
    0.2126
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    red, green, blue = (_srgb_to_linear(c) for c in rgb2rgbf(rgb))
    kr, kg, kb = WCAG_LUMINANCE_COEFFICIENTS
    return kr * red + kg * green + kb * blue


@_cached
def rgb2grayscale(rgb: Sequence[int | float]) -> RGB:
    """Convert an RGB color to the grey of the same luminance.

    Not the same as taking the saturation to zero, which holds HSL lightness
    instead and so changes how bright the color is: ``blue`` desaturated that
    way keeps HSL lightness 50 and comes out mid grey, where its luminance puts
    it close to black. This preserves :func:`rgb2relative_luminance` exactly,
    which is what makes it the one to use when the grey has to stand in for the
    color -- printing, a contrast check, a disabled state.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    RGB
        A grey, all three channels equal, with the luminance of the input.

    Raises
    ------
    InvalidColorError
        Raised when ``rgb`` is not a valid RGB value.

    Examples
    --------
    >>> rgb2grayscale((0, 0, 255))  # blue is dark, not mid grey
    RGB(red=75.96269735836901, green=75.96269735836901, blue=75.96269735836901)
    """
    channel = _threshold(_linear_to_srgb(rgb2relative_luminance(rgb)) * 255.0)
    return RGB(channel, channel, channel)


def contrast_ratio(rgb1: Sequence[int | float], rgb2: Sequence[int | float]) -> float:
    """Compute the WCAG 2.x contrast ratio between two RGB colors.

    Symmetric: the lighter of the two is always the numerator, so the order of
    the arguments does not matter.

    Alpha plays no part. A contrast ratio is between two opaque colors, and a
    translucent one has no contrast of its own -- it depends on whatever is
    behind it. Composite first, then ask.

    Parameters
    ----------
    rgb1 : Sequence[int | float]
        First RGB sequence in the ``[0, 255]`` range.
    rgb2 : Sequence[int | float]
        Second RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    float
        Contrast ratio in ``[1, 21]``: 1 for two colors of equal luminance,
        and exactly 21 for black against white.

    Raises
    ------
    InvalidColorError
        Raised when either value is not a valid RGB value.

    Examples
    --------
    >>> contrast_ratio((0, 0, 0), (255, 255, 255))
    21.0
    """
    lighter, darker = sorted(
        (rgb2relative_luminance(rgb1), rgb2relative_luminance(rgb2)), reverse=True
    )
    return (lighter + WCAG_CONTRAST_FLARE) / (darker + WCAG_CONTRAST_FLARE)


@_cached
def rgb2xyz(rgb: Sequence[int | float]) -> XYZ:
    """Convert RGB representation to CIE XYZ under the D65 illuminant.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    XYZ
        XYZ tuple scaled so that the reference white has ``y`` of 100.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    linear = [_srgb_to_linear(c) for c in rgb2rgbf(rgb)]
    x, y, z = _matrix_apply(RGB_TO_XYZ_MATRIX, linear)
    return XYZ(_threshold(x * 100.0), _threshold(y * 100.0), _threshold(z * 100.0))


@_cached
def xyz2rgb(xyz: Sequence[int | float]) -> RGB:
    """Convert CIE XYZ to RGB, clamping anything outside the sRGB gamut.

    :func:`in_srgb_gamut` says whether a given value will survive.

    Parameters
    ----------
    xyz : Sequence[int | float]
        XYZ sequence scaled so that the reference white has ``y`` of 100.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    if not is_xyz(xyz):
        raise InvalidColorError("Input is not an XYZ type.")
    linear = _matrix_apply(XYZ_TO_RGB_MATRIX, [c / 100.0 for c in xyz])
    return RGB(*(_threshold(_linear_to_srgb(c) * 255.0) for c in linear))


@_cached
def xyz2lab(xyz: Sequence[int | float]) -> LAB:
    """Convert CIE XYZ to CIE L*a*b*.

    Parameters
    ----------
    xyz : Sequence[int | float]
        XYZ sequence under D65.

    Returns
    -------
    LAB
        L*a*b* tuple with lightness in ``[0, 100]``.
    """
    if not is_xyz(xyz):
        raise InvalidColorError("Input is not an XYZ type.")

    def f(t: float) -> float:
        if t > LAB_DELTA**3:
            return float(t ** (1 / 3))
        return t / (3 * LAB_DELTA**2) + 4.0 / 29.0

    fx, fy, fz = (f(c / w) for c, w in zip(xyz, D65_WHITE_POINT, strict=True))
    return LAB(
        _threshold(116.0 * fy - 16.0),
        _threshold(500.0 * (fx - fy)),
        _threshold(200.0 * (fy - fz)),
    )


@_cached
def lab2xyz(lab: Sequence[int | float]) -> XYZ:
    """Convert CIE L*a*b* to CIE XYZ.

    Parameters
    ----------
    lab : Sequence[int | float]
        L*a*b* sequence.

    Returns
    -------
    XYZ
        XYZ tuple under D65.
    """
    if not is_lab(lab):
        raise InvalidColorError("Input is not a LAB type.")

    def f_inv(t: float) -> float:
        if t > LAB_DELTA:
            return t**3
        return 3 * LAB_DELTA**2 * (t - 4.0 / 29.0)

    fy = (lab[0] + 16.0) / 116.0
    fx = fy + lab[1] / 500.0
    fz = fy - lab[2] / 200.0
    return XYZ(
        *(
            _threshold(min(max(f_inv(c) * w, 0.0), 110.0))
            for c, w in zip((fx, fy, fz), D65_WHITE_POINT, strict=True)
        )
    )


@_cached
def lab2lch(lab: Sequence[int | float]) -> LCH:
    """Convert CIE L*a*b* to its cylindrical LCh form.

    Parameters
    ----------
    lab : Sequence[int | float]
        L*a*b* sequence.

    Returns
    -------
    LCH
        LCh tuple with hue in ``[0, 360]``.
    """
    if not is_lab(lab):
        raise InvalidColorError("Input is not a LAB type.")
    chroma = math.hypot(lab[1], lab[2])
    hue = math.degrees(math.atan2(lab[2], lab[1])) % 360.0
    return LCH(_threshold(lab[0]), _threshold(chroma), _threshold(hue))


@_cached
def lch2lab(lch: Sequence[int | float]) -> LAB:
    """Convert cylindrical CIE LCh to L*a*b*.

    Parameters
    ----------
    lch : Sequence[int | float]
        LCh sequence.

    Returns
    -------
    LAB
        L*a*b* tuple.
    """
    if not is_lch(lch):
        raise InvalidColorError("Input is not an LCH type.")
    radians = math.radians(lch[2])
    return LAB(
        _threshold(lch[0]),
        _threshold(lch[1] * math.cos(radians)),
        _threshold(lch[1] * math.sin(radians)),
    )


@_cached
def rgb2lab(rgb: Sequence[int | float]) -> LAB:
    """Convert RGB representation to CIE L*a*b*.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    LAB
        L*a*b* tuple.
    """
    return xyz2lab(rgb2xyz(rgb))


@_cached
def lab2rgb(lab: Sequence[int | float]) -> RGB:
    """Convert CIE L*a*b* to RGB representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    lab : Sequence[int | float]
        L*a*b* sequence.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    return xyz2rgb(lab2xyz(lab))


@_cached
def rgb2lch(rgb: Sequence[int | float]) -> LCH:
    """Convert RGB representation to cylindrical CIE LCh.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    LCH
        LCh tuple.
    """
    return lab2lch(rgb2lab(rgb))


@_cached
def lch2rgb(lch: Sequence[int | float]) -> RGB:
    """Convert cylindrical CIE LCh to RGB representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    lch : Sequence[int | float]
        LCh sequence.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    return lab2rgb(lch2lab(lch))


@_cached
def rgb2oklab(rgb: Sequence[int | float]) -> OKLAB:
    """Convert RGB representation to Oklab.

    Oklab hangs off sRGB directly rather than composing through
    :func:`rgb2xyz`, because its cone-response matrix is normalised against a
    more precise sRGB primary set than the seven-digit ``RGB_TO_XYZ_MATRIX``.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    OKLAB
        Oklab tuple with lightness in ``[0, 1]``.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    linear = [_srgb_to_linear(c) for c in rgb2rgbf(rgb)]
    ## Every coefficient of the matrix is positive and every linear channel is
    ## non-negative, so the cube roots below never see a negative base. They
    ## are wrapped in ``float`` because ``**`` is typed as possibly returning
    ## ``complex``.
    roots = [float(c ** (1 / 3)) for c in _matrix_apply(RGB_TO_LMS_MATRIX, linear)]
    lightness, a, b = _matrix_apply(LMS_TO_OKLAB_MATRIX, roots)
    ## a and b deliberately skip _threshold. Oklab's chroma axes are two orders
    ## of magnitude shorter than L*a*b*'s, so FLOAT_ERROR sits above the
    ## residual a grey leaves behind rather than below it, and clamping that to
    ## zero costs 2.6e-5 of a channel on the way back -- eight orders of
    ## magnitude more than the arithmetic itself loses. oklab2oklch zeroes the
    ## hue of an achromatic colour instead, which is where a hue read off
    ## floating-point noise would actually be visible.
    return OKLAB(_threshold(lightness), float(a), float(b))


@_cached
def oklab2rgb(oklab: Sequence[int | float]) -> RGB:
    """Convert Oklab to RGB, clamping anything outside the sRGB gamut.

    :func:`in_srgb_gamut` says whether a given value will survive.

    Parameters
    ----------
    oklab : Sequence[int | float]
        Oklab sequence with lightness in ``[0, 1]``.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    if not is_oklab(oklab):
        raise InvalidColorError("Input is not an OKLAB type.")
    roots = _matrix_apply(OKLAB_TO_LMS_MATRIX, oklab)
    linear = _matrix_apply(LMS_TO_RGB_MATRIX, [c**3 for c in roots])
    return RGB(*(_threshold(_linear_to_srgb(c) * 255.0) for c in linear))


@_cached
def oklab2oklch(oklab: Sequence[int | float]) -> OKLCH:
    """Convert Oklab to its cylindrical Oklch form.

    Parameters
    ----------
    oklab : Sequence[int | float]
        Oklab sequence.

    Returns
    -------
    OKLCH
        Oklch tuple with hue in ``[0, 360]``.
    """
    if not is_oklab(oklab):
        raise InvalidColorError("Input is not an OKLAB type.")
    chroma = math.hypot(oklab[1], oklab[2])
    if chroma < FLOAT_ERROR:
        ## An achromatic colour has no hue, and below FLOAT_ERROR the angle is
        ## just the direction of the noise left in a and b. Report zero rather
        ## than an arbitrary hue that a caller might interpolate through.
        return OKLCH(_threshold(oklab[0]), 0.0, 0.0)
    hue = math.degrees(math.atan2(oklab[2], oklab[1])) % 360.0
    return OKLCH(_threshold(oklab[0]), _threshold(chroma), _threshold(hue))


@_cached
def oklch2oklab(oklch: Sequence[int | float]) -> OKLAB:
    """Convert cylindrical Oklch to Oklab.

    Parameters
    ----------
    oklch : Sequence[int | float]
        Oklch sequence.

    Returns
    -------
    OKLAB
        Oklab tuple.
    """
    if not is_oklch(oklch):
        raise InvalidColorError("Input is not an OKLCH type.")
    radians = math.radians(oklch[2])
    ## a and b skip _threshold for the reason given in rgb2oklab.
    return OKLAB(
        _threshold(oklch[0]),
        float(oklch[1] * math.cos(radians)),
        float(oklch[1] * math.sin(radians)),
    )


@_cached
def rgb2oklch(rgb: Sequence[int | float]) -> OKLCH:
    """Convert RGB representation to cylindrical Oklch.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    OKLCH
        Oklch tuple.
    """
    return oklab2oklch(rgb2oklab(rgb))


@_cached
def oklch2rgb(oklch: Sequence[int | float]) -> RGB:
    """Convert cylindrical Oklch to RGB representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    oklch : Sequence[int | float]
        Oklch sequence.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    return oklab2rgb(oklch2oklab(oklch))


@_cached
def rgb2cmyk(rgb: Sequence[int | float]) -> CMYK:
    """Convert RGB representation to CMYK.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    CMYK
        CMYK tuple with each component in the ``[0, 100]`` range.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    r, g, b = rgb2rgbf(rgb)
    key = 1.0 - max(r, g, b)
    if key >= 1.0:  ## black has no chromatic component to record
        return CMYK(0.0, 0.0, 0.0, 100.0)
    scale = 1.0 - key
    return CMYK(
        _threshold((1.0 - r - key) / scale * 100.0),
        _threshold((1.0 - g - key) / scale * 100.0),
        _threshold((1.0 - b - key) / scale * 100.0),
        _threshold(key * 100.0),
    )


@_cached
def cmyk2rgb(cmyk: Sequence[int | float]) -> RGB:
    """Convert CMYK to RGB representation.

    Parameters
    ----------
    cmyk : Sequence[int | float]
        CMYK sequence with each component in the ``[0, 100]`` range.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    if not is_cmyk(cmyk):
        raise InvalidColorError("Input is not a CMYK type.")
    c, m, y, k = (component / 100.0 for component in cmyk)
    return RGB(
        _threshold((1.0 - c) * (1.0 - k) * 255.0),
        _threshold((1.0 - m) * (1.0 - k) * 255.0),
        _threshold((1.0 - y) * (1.0 - k) * 255.0),
    )


@_cached
def rgb2yuv(rgb: Sequence[int | float]) -> YUV:
    """Convert RGB representation to BT.601 YUV.

    Parameters
    ----------
    rgb : Sequence[int | float]
        RGB sequence in the ``[0, 255]`` range.

    Returns
    -------
    YUV
        YUV tuple with luma in ``[0, 1]``.
    """
    if not is_rgb(rgb):
        raise InvalidColorError("Input is not an RGB type.")
    r, g, b = rgb2rgbf(rgb)
    kr, kg, kb = YUV_LUMA_COEFFICIENTS
    luma = kr * r + kg * g + kb * b
    return YUV(
        _threshold(luma),
        _threshold(YUV_U_SCALE * (b - luma)),
        _threshold(YUV_V_SCALE * (r - luma)),
    )


@_cached
def yuv2rgb(yuv: Sequence[int | float]) -> RGB:
    """Convert BT.601 YUV to RGB representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    yuv : Sequence[int | float]
        YUV sequence with luma in ``[0, 1]``.

    Returns
    -------
    RGB
        RGB tuple in the ``[0, 255]`` range.
    """
    if not is_yuv(yuv):
        raise InvalidColorError("Input is not a YUV type.")
    luma, u, v = (float(c) for c in yuv)
    kr, kg, kb = YUV_LUMA_COEFFICIENTS
    r = luma + v / YUV_V_SCALE
    b = luma + u / YUV_U_SCALE
    g = (luma - kr * r - kb * b) / kg
    return RGB(*(_threshold(min(max(c, 0.0), 1.0) * 255.0) for c in (r, g, b)))


@_cached
def hsl2xyz(hsl: Sequence[int | float]) -> XYZ:
    """Convert HSL representation to CIE XYZ.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    XYZ
        XYZ tuple under D65.
    """
    return rgb2xyz(hsl2rgb(hsl))


@_cached
def xyz2hsl(xyz: Sequence[int | float]) -> HSL:
    """Convert CIE XYZ to HSL representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    xyz : Sequence[int | float]
        XYZ sequence under D65.

    Returns
    -------
    HSL
        HSL tuple.
    """
    return rgb2hsl(xyz2rgb(xyz))


@_cached
def hsl2lab(hsl: Sequence[int | float]) -> LAB:
    """Convert HSL representation to CIE L*a*b*.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    LAB
        L*a*b* tuple.
    """
    return rgb2lab(hsl2rgb(hsl))


@_cached
def lab2hsl(lab: Sequence[int | float]) -> HSL:
    """Convert CIE L*a*b* to HSL representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    lab : Sequence[int | float]
        L*a*b* sequence.

    Returns
    -------
    HSL
        HSL tuple.
    """
    return rgb2hsl(lab2rgb(lab))


@_cached
def hsl2lch(hsl: Sequence[int | float]) -> LCH:
    """Convert HSL representation to cylindrical CIE LCh.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    LCH
        LCh tuple.
    """
    return lab2lch(hsl2lab(hsl))


@_cached
def lch2hsl(lch: Sequence[int | float]) -> HSL:
    """Convert cylindrical CIE LCh to HSL representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    lch : Sequence[int | float]
        LCh sequence.

    Returns
    -------
    HSL
        HSL tuple.
    """
    return lab2hsl(lch2lab(lch))


@_cached
def hsl2oklab(hsl: Sequence[int | float]) -> OKLAB:
    """Convert HSL representation to Oklab.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    OKLAB
        Oklab tuple.
    """
    return rgb2oklab(hsl2rgb(hsl))


@_cached
def oklab2hsl(oklab: Sequence[int | float]) -> HSL:
    """Convert Oklab to HSL representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    oklab : Sequence[int | float]
        Oklab sequence.

    Returns
    -------
    HSL
        HSL tuple.
    """
    return rgb2hsl(oklab2rgb(oklab))


@_cached
def hsl2oklch(hsl: Sequence[int | float]) -> OKLCH:
    """Convert HSL representation to cylindrical Oklch.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    OKLCH
        Oklch tuple.
    """
    return oklab2oklch(hsl2oklab(hsl))


@_cached
def oklch2hsl(oklch: Sequence[int | float]) -> HSL:
    """Convert cylindrical Oklch to HSL representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    oklch : Sequence[int | float]
        Oklch sequence.

    Returns
    -------
    HSL
        HSL tuple.
    """
    return oklab2hsl(oklch2oklab(oklch))


@_cached
def hsl2cmyk(hsl: Sequence[int | float]) -> CMYK:
    """Convert HSL representation to CMYK.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    CMYK
        CMYK tuple.
    """
    return rgb2cmyk(hsl2rgb(hsl))


@_cached
def cmyk2hsl(cmyk: Sequence[int | float]) -> HSL:
    """Convert CMYK to HSL representation.

    Parameters
    ----------
    cmyk : Sequence[int | float]
        CMYK sequence.

    Returns
    -------
    HSL
        HSL tuple.
    """
    return rgb2hsl(cmyk2rgb(cmyk))


@_cached
def hsl2yuv(hsl: Sequence[int | float]) -> YUV:
    """Convert HSL representation to BT.601 YUV.

    Parameters
    ----------
    hsl : Sequence[int | float]
        HSL sequence as ``(h, s, l)``.

    Returns
    -------
    YUV
        YUV tuple.
    """
    return rgb2yuv(hsl2rgb(hsl))


@_cached
def yuv2hsl(yuv: Sequence[int | float]) -> HSL:
    """Convert BT.601 YUV to HSL representation.

    Anything outside the sRGB gamut is clipped, so the colour that comes
    back need not be the one that went in. :func:`in_srgb_gamut` says
    whether a given value will survive.

    Parameters
    ----------
    yuv : Sequence[int | float]
        YUV sequence.

    Returns
    -------
    HSL
        HSL tuple.
    """
    return rgb2hsl(yuv2rgb(yuv))


def _encode_unclamped(channel: float) -> float:
    """Apply the sRGB transfer function without clamping, preserving sign.

    :func:`_linear_to_srgb` clamps first, which is right when the result has to
    be a representable colour and wrong when the question is how far outside
    the gamut a colour falls. The function is odd-extended below zero so that a
    negative channel stays negative rather than folding back into range.

    Parameters
    ----------
    channel : float
        Linear-light channel, which may lie outside ``[0, 1]``.

    Returns
    -------
    float
        Gamma-encoded channel, outside ``[0, 1]`` exactly when the input was.
    """
    sign = -1.0 if channel < 0 else 1.0
    magnitude = abs(channel)
    if magnitude <= 0.0031308:
        return sign * magnitude * 12.92
    return sign * float(1.055 * magnitude ** (1 / 2.4) - 0.055)


def _unclamped_rgbf_from_xyz(xyz: Sequence[int | float]) -> tuple[float, ...]:
    """Gamma-encoded sRGB channels for an XYZ colour, clamping nothing."""
    if not is_xyz(xyz):
        raise InvalidColorError("Input is not an XYZ type.")
    linear = _matrix_apply(XYZ_TO_RGB_MATRIX, [c / 100.0 for c in xyz])
    return tuple(_encode_unclamped(c) for c in linear)


def _unclamped_rgbf_from_oklab(oklab: Sequence[int | float]) -> tuple[float, ...]:
    """Gamma-encoded sRGB channels for an Oklab colour, clamping nothing."""
    if not is_oklab(oklab):
        raise InvalidColorError("Input is not an OKLAB type.")
    roots = _matrix_apply(OKLAB_TO_LMS_MATRIX, oklab)
    linear = _matrix_apply(LMS_TO_RGB_MATRIX, [c**3 for c in roots])
    return tuple(_encode_unclamped(c) for c in linear)


def _unclamped_rgbf_from_yuv(yuv: Sequence[int | float]) -> tuple[float, ...]:
    """Gamma-encoded sRGB channels for a YUV colour, clamping nothing.

    BT.601 is defined on gamma-encoded R'G'B', so unlike the paths above there
    is no transfer function to undo here.
    """
    if not is_yuv(yuv):
        raise InvalidColorError("Input is not a YUV type.")
    luma, u, v = (float(c) for c in yuv)
    kr, kg, kb = YUV_LUMA_COEFFICIENTS
    r = luma + v / YUV_V_SCALE
    b = luma + u / YUV_U_SCALE
    g = (luma - kr * r - kb * b) / kg
    return (r, g, b)


## The spaces that can address a colour sRGB cannot show. Every other input
## format -- rgb, hsl, hsv, cmyk, hex, web and their variants -- is bounded by
## its own component ranges, so it is representable by construction and has
## nothing to ask about.
_UNCLAMPED_RGBF_FROM: dict[
    str, Callable[[Sequence[int | float]], tuple[float, ...]]
] = {
    "xyz": _unclamped_rgbf_from_xyz,
    "lab": lambda lab: _unclamped_rgbf_from_xyz(lab2xyz(lab)),
    "lch": lambda lch: _unclamped_rgbf_from_xyz(lab2xyz(lch2lab(lch))),
    "oklab": _unclamped_rgbf_from_oklab,
    "oklch": lambda oklch: _unclamped_rgbf_from_oklab(oklch2oklab(oklch)),
    "yuv": _unclamped_rgbf_from_yuv,
}


def in_srgb_gamut(
    color: Sequence[int | float], space: str, tolerance: float = 0.5
) -> bool:
    """Check whether a color is one sRGB can show, and so survives conversion.

    ``lab``, ``lch``, ``oklab``, ``oklch``, ``xyz`` and ``yuv`` all address
    colors outside sRGB. Such a value is accepted by ``Color`` and by the
    conversions, and then **clipped** -- the color that comes back is not the
    one that went in, and nothing says so. Ask this first to find out. The
    check has to happen here rather than on a finished ``Color``, which cannot
    answer it: by then the value has been clipped and the original is gone.

    The gamut boundary is sharp, and every fully saturated color sits exactly
    on it, so the ``tolerance`` matters. It is measured in 8-bit levels -- the
    units the library renders in -- and defaults to half a level, meaning "the
    clipping would not change the color as rendered". Even so, a primary
    written to two decimal places really does fall outside sRGB by more than
    that, and is reported outside, because clipping really will move it.

    Parameters
    ----------
    color : Sequence[int | float]
        Components of the color, in the space named by ``space``.
    space : str
        Space the components are in: ``"lab"``, ``"lch"``, ``"oklab"``,
        ``"oklch"``, ``"xyz"`` or ``"yuv"``.
    tolerance : float, default=0.5
        How far outside the representable range a channel may fall, in 8-bit
        levels. Pass ``0`` to test the gamut exactly.

    Returns
    -------
    bool
        ``True`` when every channel lands inside ``[0, 255]``, to within
        ``tolerance``, so the color converts to sRGB without being clipped.

    Raises
    ------
    ValueError
        Raised when ``space`` is not one of the six that can leave the gamut.
    InvalidColorError
        Raised when ``color`` is not a valid value in ``space``.

    Examples
    --------
    >>> in_srgb_gamut((53.2408, 80.0925, 67.2032), "lab")
    True
    >>> in_srgb_gamut((100, 120, -120), "lab")
    False
    """
    if space not in _UNCLAMPED_RGBF_FROM:
        raise ValueError(
            f"Cannot ask about the gamut of {space!r}. Choose one of: "
            f"{', '.join(sorted(_UNCLAMPED_RGBF_FROM))}. Every other format is "
            "bounded by its own ranges, so it is always representable."
        )
    slack = tolerance / 255.0
    return all(
        -slack <= channel <= 1.0 + slack
        for channel in _UNCLAMPED_RGBF_FROM[space](color)
    )
