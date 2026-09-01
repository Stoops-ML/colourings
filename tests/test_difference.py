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
    generator = random.Random(20260901)
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
