"""Colour difference metrics, and the nearest named colour."""

import math
import random

import pytest

from colourings import Color
from colourings.definitions import COLOR_NAME_TO_RGB
from colourings.difference import (
    _METRICS,
    delta_e_cie76,
    delta_e_cie94,
    delta_e_ciede2000,
    delta_e_ok,
    hsl_difference,
    nearest_named_hsl,
)

## Pairs differing only in lightness, where CIEDE2000 reduces to dL / SL with
## SL = 1 + 0.015 * (Lbar - 50)^2 / sqrt(20 + (Lbar - 50)^2). Computed from
## that expression rather than recorded from this implementation, so they test
## the formula instead of restating it.
LIGHTNESS_ONLY = [(0.0, 100.0), (50.0, 51.0), (0.0, 1.0), (99.0, 100.0), (20.0, 80.0)]


@pytest.mark.parametrize(("first", "second"), LIGHTNESS_ONLY)
def test_ciede2000_reduces_to_the_lightness_term_for_neutrals(first, second):
    mean = (first + second) / 2.0
    offset = mean - 50.0
    weight = 1.0 + 0.015 * offset**2 / math.sqrt(20.0 + offset**2)
    expected = abs(second - first) / weight
    assert delta_e_ciede2000((first, 0, 0), (second, 0, 0)) == pytest.approx(
        expected, abs=1e-12
    )


## The Sharma-Wu-Dalal supplementary test data, from
## https://hajim.rochester.edu/ece/sites/gsharma/ciede2000/dataNprograms/ciede2000testdata.txt
## accompanying "The CIEDE2000 Color-Difference Formula: Implementation Notes,
## Supplementary Test Data, and Mathematical Observations", G. Sharma, W. Wu and
## E. N. Dalal, Color Research and Application 30(1), 21-30, February 2005.
##
## Committed verbatim rather than fetched. CI must not need the network, and
## published test data does not change.
##
## These 34 pairs are here because every other test of this function passes
## even when the formula is wrong. Symmetry, zero-against-itself, exactly 100
## for black against white and the neutral lightness reduction all hold with a
## broken hue-rotation term or a mistyped weight, because none of them puts two
## chromatic colours on opposite sides of a hue boundary. That is what these
## pairs do: they straddle 0/360 degrees in hue, and they cluster around the
## 275-degree peak of the rotation term.
##
## Tested through the function rather than through Color, deliberately: 14 of
## these 68 Lab values are outside the sRGB gamut, so building a Color from
## them would clip the input and measure a different pair.
SHARMA_WU_DALAL = [
    ((50, 2.6772, -79.7751), (50, 0, -82.7485), 2.0425),
    ((50, 3.1571, -77.2803), (50, 0, -82.7485), 2.8615),
    ((50, 2.8361, -74.02), (50, 0, -82.7485), 3.4412),
    ((50, -1.3802, -84.2814), (50, 0, -82.7485), 1),
    ((50, -1.1848, -84.8006), (50, 0, -82.7485), 1),
    ((50, -0.9009, -85.5211), (50, 0, -82.7485), 1),
    ((50, 0, 0), (50, -1, 2), 2.3669),
    ((50, -1, 2), (50, 0, 0), 2.3669),
    ((50, 2.49, -0.001), (50, -2.49, 0.0009), 7.1792),
    ((50, 2.49, -0.001), (50, -2.49, 0.001), 7.1792),
    ((50, 2.49, -0.001), (50, -2.49, 0.0011), 7.2195),
    ((50, 2.49, -0.001), (50, -2.49, 0.0012), 7.2195),
    ((50, -0.001, 2.49), (50, 0.0009, -2.49), 4.8045),
    ((50, -0.001, 2.49), (50, 0.001, -2.49), 4.8045),
    ((50, -0.001, 2.49), (50, 0.0011, -2.49), 4.7461),
    ((50, 2.5, 0), (50, 0, -2.5), 4.3065),
    ((50, 2.5, 0), (73, 25, -18), 27.1492),
    ((50, 2.5, 0), (61, -5, 29), 22.8977),
    ((50, 2.5, 0), (56, -27, -3), 31.903),
    ((50, 2.5, 0), (58, 24, 15), 19.4535),
    ((50, 2.5, 0), (50, 3.1736, 0.5854), 1),
    ((50, 2.5, 0), (50, 3.2972, 0), 1),
    ((50, 2.5, 0), (50, 1.8634, 0.5757), 1),
    ((50, 2.5, 0), (50, 3.2592, 0.335), 1),
    ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
    ((63.0109, -31.0961, -5.8663), (62.8187, -29.7946, -4.0864), 1.263),
    ((61.2901, 3.7196, -5.3901), (61.4292, 2.248, -4.962), 1.8731),
    ((35.0831, -44.1164, 3.7933), (35.0232, -40.0716, 1.5901), 1.8645),
    ((22.7233, 20.0904, -46.694), (23.0331, 14.973, -42.5619), 2.0373),
    ((36.4612, 47.858, 18.3852), (36.2715, 50.5065, 21.2231), 1.4146),
    ((90.8027, -2.0831, 1.441), (91.1528, -1.6435, 0.0447), 1.4441),
    ((90.9257, -0.5406, -0.9208), (88.6381, -0.8985, -0.7239), 1.5381),
    ((6.7747, -0.2908, -2.4247), (5.8714, -0.0985, -2.2286), 0.6377),
    ((2.0776, 0.0795, -1.135), (0.9033, -0.0636, -0.5514), 0.9082),
]

## Half of the last digit the table publishes, and it cannot be tighter.
## The table gives four decimals; Sharma's own MATLAB reference computes pair
## 23 as 1.000049498977, which the table prints as 1.0000. Checked against a
## line-for-line port of that reference, this implementation agrees to 3e-14 --
## so the residual against the published column is the table's rounding, not
## this code's error.
PUBLISHED_PRECISION = 5e-5


def test_the_published_test_data_is_all_there():
    """Guard the guard: a truncated table would still pass every row it kept."""
    assert len(SHARMA_WU_DALAL) == 34


@pytest.mark.parametrize(("lab1", "lab2", "expected"), SHARMA_WU_DALAL)
def test_ciede2000_matches_the_published_test_data(lab1, lab2, expected):
    """The check the docstring used to say was outstanding."""
    assert delta_e_ciede2000(lab1, lab2) == pytest.approx(
        expected, abs=PUBLISHED_PRECISION
    )


def test_black_against_white_is_exactly_one_hundred():
    """The mean lightness is 50, so the lightness weight is exactly 1 and every
    other term is zero. Any drift here is a broken weight."""
    assert delta_e_ciede2000((0, 0, 0), (100, 0, 0)) == 100.0
    assert delta_e_cie76((0, 0, 0), (100, 0, 0)) == 100.0
    assert Color("black").delta_e("white") == 100.0


@pytest.mark.parametrize("metric", sorted(_METRICS))
def test_a_colour_is_no_distance_from_itself(metric):
    for name in ("red", "black", "white", "rebeccapurple", "#3d7ab8"):
        assert Color(name).delta_e(name, metric) == pytest.approx(0.0, abs=1e-12)


def test_ciede2000_is_symmetric():
    """It is symmetric by construction, and the hue wrapping rules are what
    make it so -- getting one of them wrong shows up here and nowhere else."""
    generator = random.Random(20260901)  # noqa: S311 -- a seeded sweep, not a secret
    for _ in range(2000):
        first = (
            generator.uniform(0, 100),
            generator.uniform(-128, 127),
            generator.uniform(-128, 127),
        )
        second = (
            generator.uniform(0, 100),
            generator.uniform(-128, 127),
            generator.uniform(-128, 127),
        )
        assert delta_e_ciede2000(first, second) == delta_e_ciede2000(second, first)


def test_cie94_is_deliberately_not_symmetric():
    """Its chroma and hue terms are scaled by the *first* colour's chroma. This
    is a wart of CIE94, not of the implementation, and is documented as one."""
    first, second = (50.0, 60.0, 20.0), (55.0, 10.0, -30.0)
    assert delta_e_cie94(first, second) != delta_e_cie94(second, first)


def test_cie76_overstates_the_difference_between_two_blues():
    """The known failure of plain L*a*b* distance, and the reason the later
    metrics exist. A pair of blues a couple of units apart perceptually comes
    out ten units apart in CIE76."""
    first, second = (32.0, 79.0, -104.0), (32.0, 69.0, -100.0)
    assert delta_e_cie76(first, second) > 10.0
    assert delta_e_ciede2000(first, second) < 4.0
    assert delta_e_cie94(first, second) < 4.0


def test_delta_e_ok_is_euclidean_in_oklab():
    assert delta_e_ok((0, 0, 0), (1, 0, 0)) == 1.0
    assert delta_e_ok((0.5, 0.1, -0.1), (0.5, 0.1, -0.1)) == 0.0
    assert delta_e_ok((0, 0, 0), (0, 0.3, 0.4)) == pytest.approx(0.5)


@pytest.mark.parametrize("metric", sorted(_METRICS))
def test_every_metric_grows_with_the_gap(metric):
    """Whatever the scale, further apart has to read as further apart."""
    grey = Color(rgb=(128, 128, 128))
    previous = -1.0
    for value in (128, 140, 160, 200, 255):
        difference = grey.delta_e(Color(rgb=(value, value, value)), metric)
        assert difference > previous
        previous = difference


@pytest.mark.parametrize("metric", sorted(_METRICS))
def test_a_named_colour_is_nearest_to_itself(metric):
    for name in ("red", "rebeccapurple", "mintcream", "chartreuse", "darkslategray"):
        assert Color(name).nearest_name(metric) == name


def test_nearest_name_finds_something_close_by():
    assert Color("#ff0001").nearest_name() == "red"
    assert Color("#fffffe").nearest_name() == "white"
    assert Color("#123456").nearest_name() == "midnightblue"


def test_nearest_name_is_lowercase_where_web_is_canonical():
    """The two answer slightly different questions, and only one of them is a
    spelling."""
    purple = Color("rebeccapurple")
    assert purple.nearest_name() == "rebeccapurple"
    assert purple.web == "RebeccaPurple"


def test_nearest_name_covers_every_named_colour():
    """Not a spot check: every name in the table has to be its own answer,
    which fails if the search skips entries or ties resolve unstably."""
    for name, rgb in COLOR_NAME_TO_RGB.items():
        found = Color(rgb=rgb).nearest_name()
        assert COLOR_NAME_TO_RGB[found] == rgb, (name, found)


@pytest.mark.parametrize("metric", ["cie76", "CIE-76", "cie_76", "CIEDE2000", "ok"])
def test_a_metric_may_be_spelled_loosely(metric):
    assert hsl_difference((0, 100, 50), (240, 100, 50), metric) > 0


@pytest.mark.parametrize("metric", ["cie2000", "delta_e", "euclidean", ""])
def test_an_unknown_metric_is_refused(metric):
    with pytest.raises(ValueError, match="Unknown metric"):
        hsl_difference((0, 100, 50), (240, 100, 50), metric)
    with pytest.raises(ValueError, match="Unknown metric"):
        nearest_named_hsl((0, 100, 50), metric)
    with pytest.raises(ValueError, match="Unknown metric"):
        Color("red").delta_e("blue", metric)


def test_delta_e_ignores_alpha():
    """Two colours differing only in opacity are the same colour, and how far
    apart they look depends on what is behind them."""
    assert Color("red", alpha=0.2).delta_e(Color("red", alpha=0.9)) == 0.0
