import re
from collections.abc import Sequence

from .definitions import (
    COLOR_NAME_TO_RGB,
    FLOAT_ERROR,
    LONG_HEX_COLOR,
    RGB_TO_COLOR_NAMES,
    SHORT_HEX_COLOR,
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

# add HSV, CMYK, YUV conversion


def rgb2rgba(
    rgb: Sequence[int | float], alpha: int | float
) -> tuple[float, float, float, float]:
    return rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, alpha


def hsl2hsla(
    hsl: Sequence[int | float], alpha: int | float
) -> tuple[float, float, float, float]:
    return hsl[0] / 360.0, hsl[1], hsl[2], alpha


def hsl2rgb(hsl: Sequence[int | float]) -> tuple[float, float, float]:
    """Convert HSL representation towards RGB

    :param h: Hue, position around the chromatic circle (h=1 equiv h=0)
    :param s: Saturation, color saturation (0=full gray, 1=full color)
    :param l: Ligthness, Overhaul lightness (0=full black, 1=full white)
    :rtype: 3-uple for RGB values in float between 0 and 1

    Hue, Saturation, Range from Lightness is a float between 0 and 1

    Note that Hue can be set to any value but as it is a rotation
    around the chromatic circle, any value above 1 or below 0 can
    be expressed by a value between 0 and 1 (Note that h=0 is equiv
    to h=1).

    This algorithm came from:
    http://www.easyrgb.com/index.php?X=MATH&H=19#text19
    """
    if not is_hsl(hsl):
        raise ValueError("Input is not an HSL type.")

    _h, _s, _l = [float(v) for v in hsl]
    _h /= 360.0

    if _s == 0:
        return _l * 255.0, _l * 255.0, _l * 255.0

    v2 = _l * (1.0 + _s) if _l < 0.5 else (_l + _s) - (_s * _l)

    v1 = 2.0 * _l - v2

    r = _hue2rgb(v1, v2, _h + (1.0 / 3))
    g = _hue2rgb(v1, v2, _h)
    b = _hue2rgb(v1, v2, _h - (1.0 / 3))

    return r * 255.0, g * 255.0, b * 255.0


def rgba2hsl(rgba: Sequence[int | float]) -> tuple[float, float, float]:
    if not is_rgba(rgba):
        raise ValueError("Input is not an RGBA type.")
    rgb = [v * 255.0 for v in rgba[:3]]
    return rgb2hsl(rgb)


def hsla2hsl(hsla: Sequence[int | float]) -> tuple[float, float, float]:
    if not is_hsla(hsla):
        raise ValueError("Input is not an HSLA type.")
    hsl = (hsla[0] * 360, hsla[1], hsla[2])
    return hsl


def rgb2hsl(rgb: Sequence[int | float]) -> tuple[float, float, float]:
    """Convert RGB representation towards HSL

    :param r: Red amount (float between 0 and 255)
    :param g: Green amount (float between 0 and 255)
    :param b: Blue amount (float between 0 and 255)
    :rtype: 3-uple for HSL values in float between 0 and 255

    This algorithm came from:
    http://www.easyrgb.com/index.php?X=MATH&H=19#text19
    """
    if not is_rgb(rgb):
        raise ValueError("Input is not an RGB type.")
    r, g, b = [float(v) / 255 for v in rgb]

    vmin = min(r, g, b)  ## Min. value of RGB
    vmax = max(r, g, b)  ## Max. value of RGB
    diff = vmax - vmin  ## Delta RGB value

    vsum = vmin + vmax

    _l = vsum / 2

    if diff < FLOAT_ERROR:  ## This is a gray, no chroma...
        return (0.0, 0.0, _l)

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
    elif b == vmax:
        h = (2.0 / 3) + dg - dr

    if h < 0:
        h += 1
    if h > 1:
        h -= 1

    return h * 360.0, s, _l


def _hue2rgb(v1, v2, vH):
    """Private helper function (Do not call directly)

    :param vH: rotation around the chromatic circle (between 0..1)

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


def rgb2hex(rgb: Sequence[int | float], force_long: bool = False) -> str:
    """Transform RGB tuple to hex RGB representation

    :param rgb: RGB 3-uple of float between 0 and 1
    :rtype: 3 hex char or 6 hex char string representation
    """
    if not is_rgb(rgb):
        raise ValueError("Input is not of RGB type.")

    hx = "".join([f"{int(c + 0.5 - FLOAT_ERROR):02x}" for c in rgb])

    if not force_long and hx[0::2] == hx[1::2]:
        hx = "".join(hx[0::2])

    return f"#{hx}"


def hex2rgb(hex: str) -> tuple[float, float, float]:
    """Transform hex RGB representation to RGB tuple

    :param str_rgb: 3 hex char or 6 hex char string representation
    :rtype: RGB 3-uple of float between 0 and 1
    """

    if not (is_long_hex(hex) or is_short_hex(hex)):
        raise ValueError("Input is not of hex type.")

    try:
        rgb = hex[1:]

        if len(rgb) == 6:
            r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
        elif len(rgb) == 3:
            r, g, b = rgb[0] * 2, rgb[1] * 2, rgb[2] * 2
        else:
            raise ValueError("Length of rgb must be either three or six.")
    except Exception as e:
        raise ValueError(f"Invalid value {hex} provided for rgb color.") from e

    return (float(int(r, 16)), float(int(g, 16)), float(int(b, 16)))


def hex2web(hex: str) -> str:
    """Converts HEX representation to WEB

    :param rgb: 3 hex char or 6 hex char string representation
    :rtype: web string representation (human readable if possible)

    WEB representation uses X11 rgb.txt to define conversion
    between RGB and english color names.
    """
    if not (is_long_hex(hex) or is_short_hex(hex)):
        raise ValueError("Input is not of hex type.")

    rgb = hex2rgb(hex)
    dec_rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
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


def web2hex(web: str, force_long=False) -> str:
    """Converts WEB representation to HEX

    :param rgb: web string representation (human readable if possible)
    :rtype: 3 hex char or 6 hex char string representation

    WEB representation uses X11 rgb.txt to define conversion
    between RGB and english color names.
    """
    web = web.lower()
    if web.startswith("#"):
        if LONG_HEX_COLOR.match(web) or (not force_long and SHORT_HEX_COLOR.match(web)):
            return web.lower()
        elif SHORT_HEX_COLOR.match(web) and force_long:
            return "#" + "".join([str(t) * 2 for t in web[1:]])
        raise AttributeError(f"{web} is not in web format. Need 3 or 6 hex digit.")

    if not is_web(web):
        raise ValueError("Input is not of web type.")
    return rgb2hex(
        [float(int(v)) for v in COLOR_NAME_TO_RGB[web]], force_long
    )  # convert dec to hex


def hsl2hex(hsl: Sequence[int | float]) -> str:
    if not is_hsl(hsl):
        raise ValueError("Input is not of hsl type.")
    return rgb2hex(hsl2rgb(hsl))


def hex2hsl(hex: str) -> tuple[float, float, float]:
    if not (is_long_hex(hex) or is_short_hex(hex)):
        raise ValueError("Input is not of hex type.")
    return rgb2hsl(hex2rgb(hex))


def rgb2web(rgb: Sequence[int | float]) -> str:
    if not is_rgb(rgb):
        raise ValueError("Input is not an RGB type.")
    return hex2web(rgb2hex(rgb))


def web2rgb(web: str) -> tuple[float, float, float]:
    if not is_web(web):
        raise ValueError("Input is not of web type.")
    return hex2rgb(web2hex(web))


def web2hsl(web: str) -> tuple[float, float, float]:
    if not is_web(web):
        raise ValueError("Input is not an web type.")
    return rgb2hsl(web2rgb(web))


def hsl2web(hsl: Sequence[int | float]) -> str:
    if not is_hsl(hsl):
        raise ValueError("Input is not an HSL type.")
    return rgb2web(hsl2rgb(hsl))
