"""How far apart two colors are, and what the nearest named color is.

Four metrics, in the order they were standardised. Each answers the same
question with a better model of the eye than the last, and costs more:

``cie76``
    Straight Euclidean distance in CIE L*a*b*. Fast, and wrong in a known
    direction: L*a*b* is not as uniform as it was meant to be, most visibly
    around blue, where it overstates differences.
``cie94``
    Weights lightness, chroma and hue separately, which fixes most of that.
``ciede2000``
    What "delta E" means unqualified, and the one to use unless there is a
    reason not to.
``ok``
    Euclidean distance in Oklab. As uniform as ``ciede2000`` for most pairs
    and far simpler, but its numbers are on Oklab's own scale, so a
    ``ciede2000`` threshold does not carry over.

The scales are not comparable between metrics. Roughly, on the L*a*b* three:
1 is the smallest difference a good eye can see side by side, 2 to 3 is
noticeable, and above 5 they read as different colors.

The ``ciede2000`` constants here were written from the formula rather than
copied from a reference implementation, and are checked against properties
that hold by construction -- it returns exactly 0 for a color against itself,
exactly 100 for black against white, is symmetric in its arguments, and
reduces to a hand-computable expression for a pair differing only in
lightness. They have **not** been checked against the published
Sharma-Wu-Dalal test set, which is the thing to do before relying on this for
compliance work.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from .conversions import _cached, hsl2lab, hsl2oklab, rgb2hsl
from .definitions import COLOR_NAME_TO_RGB

## CIE94, graphic-arts weighting. The textile variant uses different constants
## and is not offered, rather than offered from memory.
_CIE94_K1 = 0.045
_CIE94_K2 = 0.015


@_cached
def delta_e_cie76(lab1: Sequence[float], lab2: Sequence[float]) -> float:
    """Euclidean distance between two colors in CIE L*a*b*.

    Parameters
    ----------
    lab1 : Sequence[float]
        First color as ``(L, a, b)``.
    lab2 : Sequence[float]
        Second color as ``(L, a, b)``.

    Returns
    -------
    float
        The distance, 0 for identical colors.

    Examples
    --------
    >>> delta_e_cie76((0, 0, 0), (100, 0, 0))
    100.0
    """
    return math.dist(lab1[:3], lab2[:3])


@_cached
def delta_e_ok(oklab1: Sequence[float], oklab2: Sequence[float]) -> float:
    """Euclidean distance between two colors in Oklab.

    On Oklab's own scale, where the axes run to about 0.4 rather than to 100,
    so these numbers are much smaller than the L*a*b* metrics' and thresholds
    do not carry across.

    Parameters
    ----------
    oklab1 : Sequence[float]
        First color as ``(L, a, b)``.
    oklab2 : Sequence[float]
        Second color as ``(L, a, b)``.

    Returns
    -------
    float
        The distance, 0 for identical colors.

    Examples
    --------
    >>> delta_e_ok((0, 0, 0), (1, 0, 0))
    1.0
    """
    return math.dist(oklab1[:3], oklab2[:3])


@_cached
def delta_e_cie94(lab1: Sequence[float], lab2: Sequence[float]) -> float:
    """CIE94 difference between two colors in CIE L*a*b*.

    Splits the L*a*b* distance into lightness, chroma and hue and weights
    each, which is most of what CIE76 gets wrong. Graphic-arts weighting.

    Not symmetric: the first color is the reference, and the chroma and hue
    terms are scaled by *its* chroma. Swapping the arguments gives a slightly
    different answer, which is a known wart of CIE94 and the reason
    :func:`delta_e_ciede2000` exists.

    Parameters
    ----------
    lab1 : Sequence[float]
        The reference color as ``(L, a, b)``.
    lab2 : Sequence[float]
        The sample color as ``(L, a, b)``.

    Returns
    -------
    float
        The difference, 0 for identical colors.
    """
    lightness1, a1, b1 = lab1[:3]
    lightness2, a2, b2 = lab2[:3]
    chroma1 = math.hypot(a1, b1)
    chroma2 = math.hypot(a2, b2)
    delta_chroma = chroma1 - chroma2
    ## The hue term is what is left of the a/b distance once the chroma
    ## difference is taken out. Float error can leave that a hair below zero.
    delta_hue_squared = max(
        (a1 - a2) ** 2 + (b1 - b2) ** 2 - delta_chroma**2,
        0.0,
    )
    weight_chroma = 1.0 + _CIE94_K1 * chroma1
    weight_hue = 1.0 + _CIE94_K2 * chroma1
    return math.sqrt(
        (lightness1 - lightness2) ** 2
        + (delta_chroma / weight_chroma) ** 2
        + delta_hue_squared / weight_hue**2
    )


def _hue_angle(a: float, b: float) -> float:
    """The hue of an a/b pair, in degrees in ``[0, 360)``."""
    if a == 0.0 and b == 0.0:
        return 0.0
    return math.degrees(math.atan2(b, a)) % 360.0


@_cached
def delta_e_ciede2000(lab1: Sequence[float], lab2: Sequence[float]) -> float:
    """CIEDE2000 difference between two colors in CIE L*a*b*.

    What "delta E" means unqualified. Symmetric in its arguments, unlike
    :func:`delta_e_cie94`, which is what the hue wrapping rules below are for.

    See the module docstring on how these constants were arrived at and what
    has and has not been checked.

    Parameters
    ----------
    lab1 : Sequence[float]
        First color as ``(L, a, b)``.
    lab2 : Sequence[float]
        Second color as ``(L, a, b)``.

    Returns
    -------
    float
        The difference, 0 for identical colors and exactly 100 for black
        against white.

    Examples
    --------
    >>> delta_e_ciede2000((0, 0, 0), (100, 0, 0))
    100.0
    """
    lightness1, a1, b1 = lab1[:3]
    lightness2, a2, b2 = lab2[:3]

    ## The a axis is stretched for low-chroma colours, which is what pulls the
    ## near-neutral region into shape.
    mean_chroma = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2.0
    seventh = mean_chroma**7
    stretch = 1.0 + 0.5 * (1.0 - math.sqrt(seventh / (seventh + 25.0**7)))
    a1, a2 = a1 * stretch, a2 * stretch

    chroma1, chroma2 = math.hypot(a1, b1), math.hypot(a2, b2)
    mean_chroma = (chroma1 + chroma2) / 2.0
    hue1, hue2 = _hue_angle(a1, b1), _hue_angle(a2, b2)

    delta_lightness = lightness2 - lightness1
    delta_chroma = chroma2 - chroma1
    if chroma1 * chroma2 == 0.0:
        ## A neutral colour has no hue to differ in, and no hue to average.
        delta_hue = 0.0
        mean_hue = hue1 + hue2
    else:
        delta_hue = hue2 - hue1
        if delta_hue > 180.0:
            delta_hue -= 360.0
        elif delta_hue < -180.0:
            delta_hue += 360.0
        if abs(hue1 - hue2) <= 180.0:
            mean_hue = (hue1 + hue2) / 2.0
        elif hue1 + hue2 < 360.0:
            mean_hue = (hue1 + hue2 + 360.0) / 2.0
        else:
            mean_hue = (hue1 + hue2 - 360.0) / 2.0
    delta_hue_term = (
        2.0 * math.sqrt(chroma1 * chroma2) * math.sin(math.radians(delta_hue) / 2.0)
    )

    mean_lightness = (lightness1 + lightness2) / 2.0
    offset = mean_lightness - 50.0
    weight_lightness = 1.0 + 0.015 * offset**2 / math.sqrt(20.0 + offset**2)
    weight_chroma = 1.0 + 0.045 * mean_chroma
    hue_shape = (
        1.0
        - 0.17 * math.cos(math.radians(mean_hue - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * mean_hue))
        + 0.32 * math.cos(math.radians(3.0 * mean_hue + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * mean_hue - 63.0))
    )
    weight_hue = 1.0 + 0.015 * mean_chroma * hue_shape

    ## The rotation term, which handles the blue region where chroma and hue
    ## differences are not independent.
    seventh = mean_chroma**7
    rotation = (
        -math.sin(math.radians(60.0 * math.exp(-(((mean_hue - 275.0) / 25.0) ** 2))))
        * 2.0
        * math.sqrt(seventh / (seventh + 25.0**7))
    )

    lightness_term = delta_lightness / weight_lightness
    chroma_term = delta_chroma / weight_chroma
    hue_term = delta_hue_term / weight_hue
    return math.sqrt(
        lightness_term**2
        + chroma_term**2
        + hue_term**2
        + rotation * chroma_term * hue_term
    )


## Each metric, with the space it wants its colours in.
_METRICS: dict[str, tuple[Callable[[Sequence[float], Sequence[float]], float], str]] = {
    "cie76": (delta_e_cie76, "lab"),
    "cie94": (delta_e_cie94, "lab"),
    "ciede2000": (delta_e_ciede2000, "lab"),
    "ok": (delta_e_ok, "oklab"),
}

_TO_SPACE = {"lab": hsl2lab, "oklab": hsl2oklab}


def _resolve(
    metric: str,
) -> tuple[
    Callable[[Sequence[float], Sequence[float]], float],
    Callable[[Sequence[float]], Sequence[float]],
]:
    """Look up a metric and the conversion into the space it works in.

    Parameters
    ----------
    metric : str
        Name of the metric.

    Returns
    -------
    tuple
        The metric, and the conversion from HSL into its space.

    Raises
    ------
    ValueError
        Raised when the metric is not one of the four.
    """
    chosen = _METRICS.get(metric.replace("-", "").replace("_", "").lower())
    if chosen is None:
        raise ValueError(
            f"Unknown metric {metric!r}. Choose one of: {', '.join(sorted(_METRICS))}."
        )
    difference, space = chosen
    return difference, _TO_SPACE[space]


def hsl_difference(
    hsl1: Sequence[float], hsl2: Sequence[float], metric: str = "ciede2000"
) -> float:
    """Measure how far apart two HSL colors are, by one of the metrics.

    Parameters
    ----------
    hsl1 : Sequence[float]
        First color as ``(h, s, l)``.
    hsl2 : Sequence[float]
        Second color as ``(h, s, l)``.
    metric : str, default="ciede2000"
        One of ``"cie76"``, ``"cie94"``, ``"ciede2000"`` or ``"ok"``.

    Returns
    -------
    float
        The difference, on that metric's own scale.

    Raises
    ------
    ValueError
        Raised when ``metric`` is not one of the four.
    """
    difference, to_space = _resolve(metric)
    return difference(to_space(hsl1), to_space(hsl2))


def nearest_named_hsl(hsl: Sequence[float], metric: str = "ok") -> str:
    """Find the named color closest to an HSL color.

    Ties go to whichever name comes first in the table, so the answer is
    stable. ``ok`` is the default because it is perceptual and cheap, and this
    runs over every name.

    Parameters
    ----------
    hsl : Sequence[float]
        The color as ``(h, s, l)``.
    metric : str, default="ok"
        One of ``"cie76"``, ``"cie94"``, ``"ciede2000"`` or ``"ok"``.

    Returns
    -------
    str
        The name, lowercase, as :data:`COLOR_NAME_TO_RGB` keys them.

    Raises
    ------
    ValueError
        Raised when ``metric`` is not one of the four.

    Examples
    --------
    >>> nearest_named_hsl((0.0, 100.0, 50.0))
    'red'
    """
    difference, to_space = _resolve(metric)
    wanted = to_space(hsl)
    return min(
        COLOR_NAME_TO_RGB,
        key=lambda name: difference(wanted, to_space(rgb2hsl(COLOR_NAME_TO_RGB[name]))),
    )
