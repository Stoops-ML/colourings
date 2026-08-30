import pytest

from colourings import Color
from colourings.definitions import COLOR_NAME_TO_RGB, FLOAT_ERROR
from colourings.identify import (
    is_cmyk,
    is_hsl,
    is_hsla,
    is_hslaf,
    is_hslf,
    is_hsv,
    is_lab,
    is_lch,
    is_oklab,
    is_oklch,
    is_rgb,
    is_rgba,
    is_rgbaf,
    is_rgbf,
    is_xyz,
    is_yuv,
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


def test_is_hsv():
    assert is_hsv((0, 0, 0))
    assert is_hsv((360, 100, 100))
    assert is_hsv(Color("red").hsv)
    assert not is_hsv((361, 0, 0))
    assert not is_hsv((0, 101, 0))
    assert not is_hsv((0, 0, 101))
    assert not is_hsv((0, 0, -1))
    assert not is_hsv((0, 0))
    assert not is_hsv((0, 0, 0, 0))
    assert not is_hsv("0, 0, 0")
    assert not is_hsv(int)
    assert not is_hsv(("a", 0, 0))


def test_is_xyz():
    assert is_xyz((0, 0, 0))
    assert is_xyz(Color("red").xyz)
    assert not is_xyz((-1, 0, 0))
    assert not is_xyz((0, 0, 111))
    assert not is_xyz((0, 0))
    assert not is_xyz("0, 0, 0")


def test_is_lab():
    assert is_lab((0, 0, 0))
    assert is_lab((100, -128, 127))
    assert is_lab(Color("red").lab)
    assert not is_lab((101, 0, 0))
    assert not is_lab((0, -129, 0))
    assert not is_lab((0, 0, 128))
    assert not is_lab((0, 0))


def test_is_lch():
    assert is_lch((0, 0, 0))
    assert is_lch(Color("red").lch)
    assert not is_lch((0, -1, 0))
    assert not is_lch((0, 0, 361))
    assert not is_lch((0, 183, 0))
    assert not is_lch((0, 0))


def test_is_oklab():
    assert is_oklab((0, 0, 0))
    assert is_oklab((1, -0.4, 0.4))
    assert is_oklab(Color("red").oklab)
    assert not is_oklab((1.1, 0, 0))
    assert not is_oklab((0, -0.41, 0))
    assert not is_oklab((0, 0, 0.41))
    assert not is_oklab((0, 0))


def test_is_oklch():
    assert is_oklch((0, 0, 0))
    assert is_oklch(Color("red").oklch)
    assert not is_oklch((0, -0.01, 0))
    assert not is_oklch((0, 0, 361))
    assert not is_oklch((0, 0.41, 0))
    assert not is_oklch((0, 0))


def test_every_named_colour_is_in_oklab_range():
    """The declared bounds must hold over the whole sRGB gamut, not just red."""
    for name in COLOR_NAME_TO_RGB:
        color = Color(name)
        assert is_oklab(color.oklab)
        assert is_oklch(color.oklch)


def test_is_cmyk():
    assert is_cmyk((0, 0, 0, 0))
    assert is_cmyk(Color("red").cmyk)
    assert not is_cmyk((0, 0, 0))
    assert not is_cmyk((101, 0, 0, 0))
    assert not is_cmyk((-1, 0, 0, 0))


def test_is_yuv():
    assert is_yuv((0, 0, 0))
    assert is_yuv(Color("red").yuv)
    assert not is_yuv((1.1, 0, 0))
    assert not is_yuv((0, 0.5, 0))
    assert not is_yuv((0, 0, 0.7))
    assert not is_yuv((0, 0))
