import pytest

from colourings import Color
from colourings.definitions import COLOR_NAME_TO_RGB, FLOAT_ERROR
from colourings.identify import (
    is_hsl,
    is_hsla,
    is_hslaf,
    is_hslf,
    is_rgb,
    is_rgba,
    is_rgbaf,
    is_rgbf,
)


def test_bad_rbg():
    assert not is_rgb((300, 0, 0))
    assert not is_rgb((30, 300, 0, 0))
    assert not is_rgb("30, 300, 0, 0")
    assert not is_rgb(int)


def test_bad_rbgf():
    assert not is_rgbf((1.1, 0, 0))
    assert not is_rgbf((1.1, 2, 0, 0))
    assert not is_rgbf("30, 300, 0, 0")
    assert not is_rgbf(int)


def test_bad_rbgaf():
    assert not is_rgbaf((1.1, 0, 0))
    assert not is_rgbaf((1.1, 2, 0, 0))
    assert not is_rgbaf("30, 300, 0, 0")
    assert not is_rgbaf(int)


def test_bad_rbga():
    assert not is_rgba((255.1, 0, 0))
    assert not is_rgba((255.1, 2, 0, 0))
    assert not is_rgba("30, 300, 0, 0")
    assert not is_rgba(int)


def test_bad_hsl():
    assert not is_hsl((400, 0, 0))
    assert not is_hsl((30, 300, 0, 0))
    assert not is_hsl("30, 300, 0, 0")
    assert not is_hsl(int)


def test_bad_hsla():
    assert not is_hsla((110, 0, 0))
    assert not is_hsla((110, 200, 0, 0))
    assert not is_hsla("30, 300, 0, 0")
    assert not is_hsla(int)


def test_is_hslaf():
    assert is_hslaf((0, 0, 0, 0))
    assert is_hslaf(Color(hslaf=(0, 0, 0, 0)).hsla)
    assert not is_hslaf((2, 0, 0, 0))
    assert not is_hslaf((0, 2, 0, 0))
    assert not is_hslaf((0, 0, 2, 0))
    assert not is_hslaf((0, 0, 0, 2))
    assert not is_hslaf((-2, 0, 0, 0))
    assert not is_hslaf((0, -2, 0, 0))
    assert not is_hslaf((0, 0, -2, 0))
    assert not is_hslaf((0, 0, 0, -2))
    assert not is_hslaf("nope")
    assert not is_hslaf((0, 1, 0))


def test_is_hslf():
    assert is_hslf((0, 0, 0))
    assert is_hslf(Color(hslf=(0, 0, 0)).hslf)
    assert not is_hslf((2, 0, 0))
    assert not is_hslf((0, 2, 0))
    assert not is_hslf((0, 0, 2))
    assert not is_hslf((-2, 0, 0))
    assert not is_hslf((0, -2, 0))
    assert not is_hslf((0, 0, -2))
    assert not is_hslf("nope")
    assert not is_hslf((0, 1, 0, 0))


def test_range_check_tolerates_float_error_at_boundaries():
    """Conversions can land a hair outside the range they are meant to produce."""
    assert is_rgb((255 + FLOAT_ERROR, 0, 0))
    assert is_rgb((-FLOAT_ERROR, 0, 0))
    assert is_rgba((0, 0, 0, 255 + FLOAT_ERROR))
    assert is_rgbf((1 + FLOAT_ERROR, 0, 0))
    assert is_rgbaf((0, 0, 0, 1 + FLOAT_ERROR))
    assert is_hslf((1 + FLOAT_ERROR, 0, 0))
    assert is_hslaf((0, 0, 0, 1 + FLOAT_ERROR))
    assert is_hsl((360 + FLOAT_ERROR, 100 + FLOAT_ERROR, 100 + FLOAT_ERROR))
    assert is_hsla((360 + FLOAT_ERROR, 0, 0, 100 + FLOAT_ERROR))


def test_range_check_still_rejects_beyond_the_tolerance():
    """The tolerance is FLOAT_ERROR, not an open door."""
    assert not is_rgb((255 + 2 * FLOAT_ERROR, 0, 0))
    assert not is_rgb((-2 * FLOAT_ERROR, 0, 0))
    assert not is_rgbf((1 + 2 * FLOAT_ERROR, 0, 0))
    assert not is_hsl((360 + 2 * FLOAT_ERROR, 0, 0))
    assert not is_hsl((0, 100 + 2 * FLOAT_ERROR, 0))
    assert not is_hsla((0, 0, 0, 100 + 2 * FLOAT_ERROR))


def test_hue_component_is_type_checked():
    """A non-numeric hue used to slip through unchecked."""
    assert not is_hsl(("a", 0, 0))
    assert not is_hsl((None, 0, 0))
    assert not is_hsla(("a", 0, 0, 0))
    assert not is_hsla((None, 0, 0, 0))


@pytest.mark.parametrize(
    "name",
    [
        "mintcream",
        "ghostwhite",
        "lightpink",
        "peachpuff",
        "moccasin",
        "papayawhip",
        "snow",
    ],
)
def test_named_colors_whose_saturation_overshoots_100(name):
    """rgb2hsl returns e.g. 100.00000000000028 for these, which used to raise."""
    assert Color(name).hex_l == Color(web=name).hex_l


def test_every_named_color_is_constructible():
    for name in COLOR_NAME_TO_RGB:
        c = Color(name)
        assert Color(hsl=c.hsl).hex_l == c.hex_l
        assert Color(rgb=c.rgb).hex_l == c.hex_l
