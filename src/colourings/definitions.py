import re
from typing import NamedTuple

## Soften inequalities and some rounding issue based on float
FLOAT_ERROR = 0.0000005


## Colour representations. Each is a tuple subclass, so it stays interchangeable
## with the plain tuples previously returned by the conversion functions while
## naming its components and distinguishing the 0-255/0-360 scales from the
## normalised ``f`` variants.


class RGB(NamedTuple):
    """Red, green and blue components in the ``[0, 255]`` range."""

    red: float
    green: float
    blue: float


class RGBA(NamedTuple):
    """Red, green, blue and alpha components in the ``[0, 255]`` range."""

    red: float
    green: float
    blue: float
    alpha: float


class RGBf(NamedTuple):
    """Red, green and blue components normalised to the ``[0, 1]`` range."""

    red: float
    green: float
    blue: float


class RGBAf(NamedTuple):
    """Red, green, blue and alpha components normalised to the ``[0, 1]`` range."""

    red: float
    green: float
    blue: float
    alpha: float


class HSL(NamedTuple):
    """Hue in ``[0, 360]`` with saturation and lightness in ``[0, 100]``."""

    hue: float
    saturation: float
    lightness: float


class HSV(NamedTuple):
    """Hue in ``[0, 360]`` with saturation and value in ``[0, 100]``."""

    hue: float
    saturation: float
    value: float


class XYZ(NamedTuple):
    """CIE 1931 XYZ tristimulus values, scaled so that Y is in ``[0, 100]``."""

    x: float
    y: float
    z: float


class LAB(NamedTuple):
    """CIE L*a*b* with lightness in ``[0, 100]`` and a/b in ``[-128, 127]``."""

    lightness: float
    a: float
    b: float


class LCH(NamedTuple):
    """Cylindrical CIE L*a*b*: lightness, chroma, and hue in ``[0, 360]``."""

    lightness: float
    chroma: float
    hue: float


class OKLAB(NamedTuple):
    """Oklab with lightness in ``[0, 1]`` and a/b within ``[-0.4, 0.4]``."""

    lightness: float
    a: float
    b: float


class OKLCH(NamedTuple):
    """Cylindrical Oklab: lightness, chroma in ``[0, 0.4]``, hue in ``[0, 360]``."""

    lightness: float
    chroma: float
    hue: float


class CMYK(NamedTuple):
    """Cyan, magenta, yellow and key, each in ``[0, 100]``."""

    cyan: float
    magenta: float
    yellow: float
    key: float


class YUV(NamedTuple):
    """BT.601 luma in ``[0, 1]`` with chroma differences around zero."""

    luma: float
    u: float
    v: float


class HSLA(NamedTuple):
    """Hue in ``[0, 360]`` with saturation, lightness and alpha in ``[0, 100]``."""

    hue: float
    saturation: float
    lightness: float
    alpha: float


class HSLf(NamedTuple):
    """Hue, saturation and lightness normalised to the ``[0, 1]`` range."""

    hue: float
    saturation: float
    lightness: float


class HSLAf(NamedTuple):
    """Hue, saturation, lightness and alpha normalised to the ``[0, 1]`` range."""

    hue: float
    saturation: float
    lightness: float
    alpha: float


## Source data, written as integers to keep the table readable. The public
## mappings below expose it with float components.
_NAMED_RGB: dict[tuple[int, int, int], list[str]] = {
    (0, 0, 0): ["Black"],
    (0, 0, 128): ["Navy", "NavyBlue"],
    (0, 0, 139): ["DarkBlue"],
    (0, 0, 205): ["MediumBlue"],
    (0, 0, 255): ["Blue"],
    (0, 100, 0): ["DarkGreen"],
    (0, 128, 0): ["Green"],
    (0, 139, 139): ["DarkCyan"],
    (0, 128, 128): ["Teal"],
    (0, 191, 255): ["DeepSkyBlue"],
    (0, 206, 209): ["DarkTurquoise"],
    (0, 250, 154): ["MediumSpringGreen"],
    (0, 255, 0): ["Lime"],
    (0, 255, 127): ["SpringGreen"],
    (0, 255, 255): ["Cyan", "Aqua"],
    (25, 25, 112): ["MidnightBlue"],
    (30, 144, 255): ["DodgerBlue"],
    (32, 178, 170): ["LightSeaGreen"],
    (34, 139, 34): ["ForestGreen"],
    (46, 139, 87): ["SeaGreen"],
    (47, 79, 79): ["DarkSlateGray", "DarkSlateGrey"],
    (50, 205, 50): ["LimeGreen"],
    (60, 179, 113): ["MediumSeaGreen"],
    (64, 224, 208): ["Turquoise"],
    (65, 105, 225): ["RoyalBlue"],
    (70, 130, 180): ["SteelBlue"],
    (72, 61, 139): ["DarkSlateBlue"],
    (72, 209, 204): ["MediumTurquoise"],
    (75, 0, 130): ["Indigo"],
    (85, 107, 47): ["DarkOliveGreen"],
    (95, 158, 160): ["CadetBlue"],
    (100, 149, 237): ["CornflowerBlue"],
    (102, 51, 153): ["RebeccaPurple"],
    (102, 205, 170): ["MediumAquamarine"],
    (105, 105, 105): ["DimGray", "DimGrey"],
    (106, 90, 205): ["SlateBlue"],
    (107, 142, 35): ["OliveDrab"],
    (112, 128, 144): ["SlateGray", "SlateGrey"],
    (119, 136, 153): ["LightSlateGray", "LightSlateGrey"],
    (123, 104, 238): ["MediumSlateBlue"],
    (124, 252, 0): ["LawnGreen"],
    (127, 255, 0): ["Chartreuse"],
    (127, 255, 212): ["Aquamarine"],
    (128, 0, 0): ["Maroon"],
    (128, 0, 128): ["Purple"],
    (128, 128, 0): ["Olive"],
    (128, 128, 128): ["Gray", "Grey"],
    (132, 112, 255): ["LightSlateBlue"],
    (135, 206, 235): ["SkyBlue"],
    (135, 206, 250): ["LightSkyBlue"],
    (138, 43, 226): ["BlueViolet"],
    (139, 0, 0): ["DarkRed"],
    (139, 0, 139): ["DarkMagenta"],
    (139, 69, 19): ["SaddleBrown"],
    (143, 188, 143): ["DarkSeaGreen"],
    (144, 238, 144): ["LightGreen"],
    (147, 112, 219): ["MediumPurple"],
    (148, 0, 211): ["DarkViolet"],
    (152, 251, 152): ["PaleGreen"],
    (153, 50, 204): ["DarkOrchid"],
    (154, 205, 50): ["YellowGreen"],
    (160, 82, 45): ["Sienna"],
    (165, 42, 42): ["Brown"],
    (169, 169, 169): ["DarkGray", "DarkGrey"],
    (173, 216, 230): ["LightBlue"],
    (173, 255, 47): ["GreenYellow"],
    (175, 238, 238): ["PaleTurquoise"],
    (176, 196, 222): ["LightSteelBlue"],
    (176, 224, 230): ["PowderBlue"],
    (178, 34, 34): ["Firebrick"],
    (184, 134, 11): ["DarkGoldenrod"],
    (186, 85, 211): ["MediumOrchid"],
    (188, 143, 143): ["RosyBrown"],
    (189, 183, 107): ["DarkKhaki"],
    (192, 192, 192): ["Silver"],
    (199, 21, 133): ["MediumVioletRed"],
    (205, 92, 92): ["IndianRed"],
    (205, 133, 63): ["Peru"],
    (208, 32, 144): ["VioletRed"],
    (210, 105, 30): ["Chocolate"],
    (210, 180, 140): ["Tan"],
    (211, 211, 211): ["LightGray", "LightGrey"],
    (216, 191, 216): ["Thistle"],
    (218, 112, 214): ["Orchid"],
    (218, 165, 32): ["Goldenrod"],
    (219, 112, 147): ["PaleVioletRed"],
    (220, 20, 60): ["Crimson"],
    (220, 220, 220): ["Gainsboro"],
    (221, 160, 221): ["Plum"],
    (222, 184, 135): ["Burlywood"],
    (224, 255, 255): ["LightCyan"],
    (230, 230, 250): ["Lavender"],
    (233, 150, 122): ["DarkSalmon"],
    (238, 130, 238): ["Violet"],
    (238, 221, 130): ["LightGoldenrod"],
    (238, 232, 170): ["PaleGoldenrod"],
    (240, 128, 128): ["LightCoral"],
    (240, 230, 140): ["Khaki"],
    (240, 248, 255): ["AliceBlue"],
    (240, 255, 240): ["Honeydew"],
    (240, 255, 255): ["Azure"],
    (244, 164, 96): ["SandyBrown"],
    (245, 222, 179): ["Wheat"],
    (245, 245, 220): ["Beige"],
    (245, 245, 245): ["WhiteSmoke"],
    (245, 255, 250): ["MintCream"],
    (248, 248, 255): ["GhostWhite"],
    (250, 128, 114): ["Salmon"],
    (250, 235, 215): ["AntiqueWhite"],
    (250, 240, 230): ["Linen"],
    (250, 250, 210): ["LightGoldenrodYellow"],
    (253, 245, 230): ["OldLace"],
    (255, 0, 0): ["Red"],
    (255, 0, 255): ["Magenta", "Fuchsia"],
    (255, 20, 147): ["DeepPink"],
    (255, 69, 0): ["OrangeRed"],
    (255, 99, 71): ["Tomato"],
    (255, 105, 180): ["HotPink"],
    (255, 127, 80): ["Coral"],
    (255, 140, 0): ["DarkOrange"],
    (255, 160, 122): ["LightSalmon"],
    (255, 165, 0): ["Orange"],
    (255, 182, 193): ["LightPink"],
    (255, 192, 203): ["Pink"],
    (255, 215, 0): ["Gold"],
    (255, 218, 185): ["PeachPuff"],
    (255, 222, 173): ["NavajoWhite"],
    (255, 228, 181): ["Moccasin"],
    (255, 228, 196): ["Bisque"],
    (255, 228, 225): ["MistyRose"],
    (255, 235, 205): ["BlanchedAlmond"],
    (255, 239, 213): ["PapayaWhip"],
    (255, 240, 245): ["LavenderBlush"],
    (255, 245, 238): ["Seashell"],
    (255, 248, 220): ["Cornsilk"],
    (255, 250, 205): ["LemonChiffon"],
    (255, 250, 240): ["FloralWhite"],
    (255, 250, 250): ["Snow"],
    (255, 255, 0): ["Yellow"],
    (255, 255, 224): ["LightYellow"],
    (255, 255, 240): ["Ivory"],
    (255, 255, 255): ["White"],
}

## Linear sRGB <-> CIE XYZ under D65 (IEC 61966-2-1).
RGB_TO_XYZ_MATRIX = (
    (0.4124564, 0.3575761, 0.1804375),
    (0.2126729, 0.7151522, 0.0721750),
    (0.0193339, 0.1191920, 0.9503041),
)


def _invert_3x3(
    matrix: tuple[tuple[float, float, float], ...],
) -> tuple[tuple[float, float, float], ...]:
    """Invert a 3x3 matrix by cofactor expansion.

    Parameters
    ----------
    matrix : tuple[tuple[float, float, float], ...]
        Three rows of three coefficients.

    Returns
    -------
    tuple[tuple[float, float, float], ...]
        The inverse, as three rows of three coefficients.
    """
    (a, b, c), (d, e, f), (g, h, i) = matrix
    cofactors = (
        (e * i - f * h, c * h - b * i, b * f - c * e),
        (f * g - d * i, a * i - c * g, c * d - a * f),
        (d * h - e * g, b * g - a * h, a * e - b * d),
    )
    determinant = a * cofactors[0][0] + b * cofactors[1][0] + c * cofactors[2][0]
    return tuple(
        (row[0] / determinant, row[1] / determinant, row[2] / determinant)
        for row in cofactors
    )


## Derived rather than quoted, for the same reason as the white point below:
## the published inverse is rounded to seven digits and is not the exact
## inverse of the matrix above, which costs about 4e-4 of a channel on an
## RGB -> XYZ -> RGB round trip. Deriving it brings that down to float noise.
XYZ_TO_RGB_MATRIX = _invert_3x3(RGB_TO_XYZ_MATRIX)

## Reference white for the CIE conversions. sRGB is defined against D65, so
## that is the illuminant used throughout; values are not interchangeable with
## a library that uses D50.
##
## Derived from the matrix rather than quoted, because the published
## coefficients are rounded and their green row sums to 1.0000001. Quoting the
## nominal (95.047, 100.0, 108.883) would put white at L* 100.0000039, just
## outside the range L* is defined over. Deriving it makes white land exactly
## on the white point, so L* of white is exactly 100.
D65_WHITE_POINT: tuple[float, float, float] = (
    sum(RGB_TO_XYZ_MATRIX[0]) * 100.0,
    sum(RGB_TO_XYZ_MATRIX[1]) * 100.0,
    sum(RGB_TO_XYZ_MATRIX[2]) * 100.0,
)

## Breakpoint of the L*a*b* transfer function, delta = 6/29.
LAB_DELTA = 6.0 / 29.0

## WCAG 2.x relative luminance: the weights the standard gives for combining
## linear-light sRGB channels, and the flare term added to both sides of a
## contrast ratio so that black against white comes to exactly 21.
##
## Not to be confused with YUV_LUMA_COEFFICIENTS below. Those are BT.601's, for
## a different set of primaries, and are applied to the channels as encoded
## rather than to linear light. `Color.luminance` uses those; anything about
## contrast must use these.
WCAG_LUMINANCE_COEFFICIENTS = (0.2126, 0.7152, 0.0722)
WCAG_CONTRAST_FLARE = 0.05

## The minimum contrast ratio WCAG 2.x asks for, by conformance level and text
## size. "Large" means 18pt, or 14pt bold; anything smaller is "normal". Note
## that AA large and AAA normal are the same 4.5 from opposite directions.
WCAG_CONTRAST_MINIMUMS: dict[tuple[str, str], float] = {
    ("AA", "normal"): 4.5,
    ("AA", "large"): 3.0,
    ("AAA", "normal"): 7.0,
    ("AAA", "large"): 4.5,
}

## BT.601 luma coefficients, with the scale factors that turn the B-Y and R-Y
## differences into U and V. Working from the differences rather than a rounded
## 3x3 matrix keeps a grey at exactly U = V = 0; the published matrix leaves
## white at U = 1e-5.
YUV_LUMA_COEFFICIENTS = (0.299, 0.587, 0.114)
YUV_U_SCALE = 0.492
YUV_V_SCALE = 0.877

## Oklab (Ottosson, 2020). Linear sRGB to the cone-response space, then
## the cube-rooted cone responses to Oklab.
##
## Both are quoted rather than derived, which is the opposite of the choice
## made for XYZ above, because here the published coefficients are the
## self-consistent ones: the rows of the first matrix sum to 1 to within 1e-10,
## so white reaches (1, 1, 1). Building it instead from the published
## XYZ-to-cone matrix and the seven-digit RGB_TO_XYZ_MATRIX would put white at
## (0.99993, 1.00002, 1.00034), a 3.4e-4 error that gives every grey a faint
## cast. Oklab therefore hangs off sRGB directly and does not pass through XYZ.
RGB_TO_LMS_MATRIX = (
    (0.4122214708, 0.5363325363, 0.0514459929),
    (0.2119034982, 0.6806995451, 0.1073969566),
    (0.0883024619, 0.2817188376, 0.6299787005),
)

## The first row sums to 0.9999999935, so white lands 6.5e-9 short of L = 1;
## the other two rows put a and b of a neutral within FLOAT_ERROR of zero,
## where _threshold takes them to exactly zero.
LMS_TO_OKLAB_MATRIX = (
    (0.2104542553, 0.7936177850, -0.0040720468),
    (1.9779984951, -2.4285922050, 0.4505937099),
    (0.0259040371, 0.7827717662, -0.8086757660),
)

## Derived for the same reason as XYZ_TO_RGB_MATRIX: the published inverses are
## rounded to ten digits and are not the exact inverses of the matrices they
## undo. Composing each published pair leaves the identity out by 1.6e-10 and
## 3.7e-8 respectively; inverting brings both to 5.6e-16. The derived values
## agree with the published ones to eight decimal places.
LMS_TO_RGB_MATRIX = _invert_3x3(RGB_TO_LMS_MATRIX)
OKLAB_TO_LMS_MATRIX = _invert_3x3(LMS_TO_OKLAB_MATRIX)

RGB_TO_COLOR_NAMES: dict[RGB, list[str]] = {
    RGB(float(r), float(g), float(b)): names for (r, g, b), names in _NAMED_RGB.items()
}

## Building inverse relation
COLOR_NAME_TO_RGB: dict[str, RGB] = {
    name.lower(): rgb for rgb, names in RGB_TO_COLOR_NAMES.items() for name in names
}


LONG_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
SHORT_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{3}$")

## The same two forms with an alpha pair or digit on the end, as CSS
## Color 4 allows. Kept separate from the pair above so that the length
## alone still says whether a hex string carries an alpha.
LONG_HEX_ALPHA_COLOR = re.compile(r"^#[0-9a-fA-F]{8}$")
SHORT_HEX_ALPHA_COLOR = re.compile(r"^#[0-9a-fA-F]{4}$")


def linspace(
    start: int | float, stop: int | float, num: int, endpoint: bool = True
) -> list[float]:
    """Return evenly spaced values over a numeric interval.

    Parameters
    ----------
    start : int | float
        Start value of the interval.
    stop : int | float
        End value of the interval.
    num : int
        Number of samples to generate.
    endpoint : bool, default=True
        Whether to include ``stop`` as the final sample.

    Returns
    -------
    list[float]
        Evenly spaced floating-point values between ``start`` and ``stop``.
    """
    if num <= 0:
        return []
    if num == 1:
        return [start]
    step = (stop - start) / (num - 1) if endpoint else (stop - start) / num
    result = [float(start + step * i) for i in range(num)]
    if endpoint:
        ## `start + step * (num - 1)` is not reliably `stop`: it lands a unit in
        ## the last place away for about one interval in six, so the final
        ## sample is assigned rather than computed. The docstring promises
        ## `stop` is included, and a caller interpolating an alpha needs that
        ## literally -- `Color.alpha` rejects 1.0000000000000002 outright,
        ## its range check having none of the float tolerance `is_hsl` has.
        result[-1] = float(stop)
    return result
