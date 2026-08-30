from unittest.mock import patch

import pytest

from colourings.conversions import (
    clear_caches,
    hex2hsl,
    hex2hsv,
    hex2rgb,
    hex2web,
    hsl2hex,
    hsl2hsla,
    hsl2hslaf,
    hsl2hslf,
    hsl2hsv,
    hsl2rgb,
    hsl2rgbf,
    hsl2web,
    hsla2hsl,
    hslf2hsl,
    hsv2hex,
    hsv2hsl,
    hsv2rgb,
    hsv2web,
    rgb2hex,
    rgb2hsl,
    rgb2hsv,
    rgb2web,
    rgba2hsl,
    rgbaf2hsl,
    rgbf2hsl,
    rgbf2rgb,
    web2hex,
    web2hsl,
    web2hsv,
    web2rgb,
)
from colourings.errors import InvalidColorError


def test_rgb2web():
    assert rgb2web((0, 0, 0)) == "black"
    assert rgb2web((0.0, 0.0, 0.0)) == "black"


def test_web2rgb():
    assert web2rgb("black") == (0.0, 0.0, 0.0)


def test_web2hsl():
    hsl = web2hsl("grey")
    assert hsl[0] == 0.0
    assert hsl[1] == 0.0
    assert round(hsl[2], 4) == 50.1961
    hsl1 = web2hsl("grey")
    assert hsl1[0] == 0.0
    assert hsl1[1] == 0.0
    assert round(hsl1[2], 4) == 50.1961


def test_hsl2web():
    assert hsl2web((0.0, 0.0, 50.20)) == "gray"


def test_hex2hsl():
    hsl = hex2hsl("#00ff00")
    assert round(hsl[0] / 360.0, 4) == 0.3333
    assert hsl[1] == 100.0
    assert hsl[2] == 50


def test_hsl2hex():
    assert hsl2hex((100.0, 100.0, 100.0)) == "#fff"


def test_hex2web_7_to_4_digits():
    assert hex2web("#112233") == "#123"


def test_web2hex():
    assert web2hex("#123", True) == "#112233"


def test_bad_rgbaf2hsl():
    with pytest.raises(ValueError):
        rgbaf2hsl("a")  # type: ignore
    with pytest.raises(ValueError):
        rgbaf2hsl((2, 0, 0, 0))
    with pytest.raises(ValueError):
        rgbaf2hsl((0, 2, 0, 0))
    with pytest.raises(ValueError):
        rgbaf2hsl((0, 0, 2, 0))
    with pytest.raises(ValueError):
        rgbaf2hsl((0, 0, 0, 2))


def test_bad_rgba2hsl():
    with pytest.raises(ValueError):
        rgba2hsl("a")  # type: ignore
    with pytest.raises(ValueError):
        rgba2hsl((256, 0, 0, 0))
    with pytest.raises(ValueError):
        rgba2hsl((0, 256, 0, 0))
    with pytest.raises(ValueError):
        rgba2hsl((0, 0, 256, 0))
    with pytest.raises(ValueError):
        rgba2hsl((0, 0, 0, 256))


def test_bad_rgbf2hsl():
    with pytest.raises(ValueError):
        rgbf2hsl("a")  # type: ignore
    with pytest.raises(ValueError):
        rgbf2hsl((1.1, 0, 0, 0))
    with pytest.raises(ValueError):
        rgbf2hsl((0, 1.1, 0, 0))
    with pytest.raises(ValueError):
        rgbf2hsl((0, 0, 1.1, 0))
    with pytest.raises(ValueError):
        rgbf2hsl((0, 0, 0, 1.1))


def test_bad_hsla2hsl():
    with pytest.raises(ValueError):
        hsla2hsl("a")  # type: ignore
    with pytest.raises(ValueError):
        hsla2hsl((370, 0, 0, 0))
    with pytest.raises(ValueError):
        hsla2hsl((0, 200, 0, 0))
    with pytest.raises(ValueError):
        hsla2hsl((0, 0, 200, 0))
    with pytest.raises(ValueError):
        hsla2hsl((0, 0, 0, 200))


def test_bad_hex2web():
    with pytest.raises(ValueError):
        hex2web("black")


def test_bad_web2hex():
    ## A malformed hex used to raise AttributeError here, which is neither
    ## accurate nor catchable alongside every other bad-colour error.
    with pytest.raises(InvalidColorError):
        web2hex("#1234")
    with pytest.raises(InvalidColorError):
        web2hex("123")


def test_bad_web2rgb():
    with pytest.raises(ValueError):
        web2rgb("#1234")
    with pytest.raises(ValueError):
        web2rgb("123")


def test_bad_web2hsl():
    with pytest.raises(ValueError):
        web2hsl("#1234")
    with pytest.raises(ValueError):
        web2hsl("123")


def test_bad_hsl2web():
    with pytest.raises(ValueError):
        hsl2web("a")  # type: ignore
    with pytest.raises(ValueError):
        hsl2web((0, 0, 0, 0))
    with pytest.raises(ValueError):
        hsl2web((361, 0, 0))
    with pytest.raises(ValueError):
        hsl2web((0, 110, 0))
    with pytest.raises(ValueError):
        hsl2web((0, 0, 110))


def test_bad_hsl2hex():
    with pytest.raises(ValueError):
        hsl2hex("a")  # type: ignore
    with pytest.raises(ValueError):
        hsl2hex((0, 0, 0, 0))
    with pytest.raises(ValueError):
        hsl2hex((361, 0, 0))
    with pytest.raises(ValueError):
        hsl2web((0, 110, 0))
    with pytest.raises(ValueError):
        hsl2web((0, 0, 110))


def test_bad_hex2hsl():
    with pytest.raises(ValueError):
        hex2hsl("black")
    with pytest.raises(ValueError):
        hex2hsl("#black")


def test_bad_rgb2web():
    with pytest.raises(ValueError):
        rgb2web("a")  # type: ignore
    with pytest.raises(ValueError):
        rgb2web((1, 0, 0, 0))
    with pytest.raises(ValueError):
        rgb2web((-1, 0, 0))


def test_bad_hsl2rgb():
    with pytest.raises(ValueError):
        hsl2rgb((0, 102, 0))
    with pytest.raises(ValueError):
        hsl2rgb((0, 0, 102))
    with pytest.raises(ValueError):
        hsl2rgb((0, 0, -1))
    with pytest.raises(ValueError):
        hsl2rgb((0, -1, 0))


def test_bad_rgb2hex():
    with pytest.raises(ValueError):
        rgb2hex((-1, 0, 0, 0))
    with pytest.raises(ValueError):
        rgb2hex((260, 0, 0))


def test_bad_rgb2hsl():
    with pytest.raises(ValueError):
        rgb2hsl((0, 0, -1))
    with pytest.raises(ValueError):
        rgb2hsl((0, -1, 0))
    with pytest.raises(ValueError):
        rgb2hsl((-1, 0, 0))


def test_bad_hex2rgb():
    with pytest.raises(ValueError):
        hex2rgb("#00ff000")


def test_hex2rgb_defensive_invalid_length_branch():
    with (
        patch("colourings.conversions.is_long_hex", return_value=True),
        patch("colourings.conversions.is_short_hex", return_value=False),
        pytest.raises(ValueError, match="Invalid value #1234 provided for rgb color"),
    ):
        hex2rgb("#1234")


def test_rgb2hsl_normalizes_hue_above_one_branch():
    with patch("builtins.min", return_value=0.9):
        hue, saturation, lightness = rgb2hsl((0, 255, 255))

    assert round(hue, 6) == 360.0
    assert saturation > 0
    assert lightness > 0


def test_bad_hsl2hsla():
    with pytest.raises(ValueError):
        hsl2hsla((-1, 0, 0), 1)


def test_bad_hsl2hslaf():
    with pytest.raises(ValueError):
        hsl2hslaf((-1, 0, 0), 1)


def test_bad_hslf2hsl():
    with pytest.raises(ValueError):
        hslf2hsl((-1, 0, 0))


def test_bad_hsl2hslf():
    with pytest.raises(ValueError):
        hsl2hslf((-1, 0, 0))


def test_cache_accepts_unhashable_sequences():
    """Lists are accepted even though ``lru_cache`` cannot key on them."""
    assert rgb2hsl([255, 0, 0]) == rgb2hsl((255, 0, 0))
    assert hsl2rgb([0, 100, 50]) == hsl2rgb((0, 100, 50))
    assert rgb2hex([255, 0, 0]) == rgb2hex((255, 0, 0))


def test_cache_shares_entry_between_list_and_tuple():
    """A list and the equivalent tuple hit the same cache entry."""
    first = rgb2hsl([255, 0, 0])
    assert rgb2hsl((255, 0, 0)) is first


def test_cache_returns_memoized_result():
    """Repeated calls return the identical object, so the result was cached."""
    assert rgb2hsl((255, 0, 0)) is rgb2hsl((255, 0, 0))
    assert web2hsl("rebeccapurple") is web2hsl("rebeccapurple")
    assert web2rgb("rebeccapurple") is web2rgb("rebeccapurple")


def test_cache_distinguishes_arguments():
    assert rgb2hex((255, 0, 0), force_long=True) != rgb2hex((255, 0, 0))
    assert rgb2hsl((255, 0, 0)) != rgb2hsl((0, 255, 0))


def test_clear_caches_forces_recomputation():
    first = rgb2hsl((255, 0, 0))
    assert rgb2hsl((255, 0, 0)) is first
    clear_caches()
    assert rgb2hsl((255, 0, 0)) == first
    assert rgb2hsl((255, 0, 0)) is not first


def test_cache_does_not_mask_validation_errors():
    """Invalid input raises the conversion's own error, not a cache error."""
    with pytest.raises(ValueError):
        rgb2hsl((300, 0, 0))
    with pytest.raises(ValueError):
        rgb2hsl((300, 0, 0))


def test_unhashable_non_sequence_raises_conversion_error():
    """A set is unhashable and not a sequence: the conversion still rejects it."""
    with pytest.raises(ValueError):
        rgb2hsl({255, 0, 1})  # type: ignore


def test_rgbf2rgb():
    assert rgbf2rgb((1.0, 0.5, 0.0)) == (255.0, 127.5, 0.0)
    assert rgbf2rgb((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)


def test_bad_hsl2rgbf():
    with pytest.raises(ValueError):
        hsl2rgbf((361, 0, 0))
    with pytest.raises(ValueError):
        hsl2rgbf((0, 110, 0))
    with pytest.raises(ValueError):
        hsl2rgbf("a")  # type: ignore


def test_hsl2rgbf_does_not_round_trip_through_0_255():
    """Normalized output keeps full precision.

    Scaling to ``[0, 255]`` and back down would return 0.8993999999999999.
    """
    assert hsl2rgbf((28, 9, 90)) == (0.909, 0.8994, 0.891)


def test_normalized_and_scaled_paths_agree():
    """The 0-1 and 0-255 conversions stay consistent with each other."""
    for hsl in [(0, 100, 50), (28, 9, 90), (240, 100, 50), (180, 0, 25)]:
        assert hsl2rgbf(hsl) == pytest.approx([v / 255.0 for v in hsl2rgb(hsl)])

    for rgb in [(255, 0, 0), (12, 200, 37), (0, 0, 0), (255, 255, 255)]:
        rgbf = tuple(v / 255.0 for v in rgb)
        assert rgbf2hsl(rgbf) == pytest.approx(rgb2hsl(rgb))
        assert rgbaf2hsl((*rgbf, 1.0)) == pytest.approx(rgb2hsl(rgb))


def test_hsla2hsl_returns_floats_for_integer_input():
    """hsla2hsl used to pass its input through without normalizing it."""
    hsl = hsla2hsl((240, 100, 50, 100))
    assert hsl == (240.0, 100.0, 50.0)
    assert [type(v) for v in hsl] == [float, float, float]


HSV_CASES = [
    ## (rgb, hsv) -- reference values from the HSV definition
    ((255, 0, 0), (0.0, 100.0, 100.0)),
    ((0, 255, 0), (120.0, 100.0, 100.0)),
    ((0, 0, 255), (240.0, 100.0, 100.0)),
    ((255, 255, 255), (0.0, 0.0, 100.0)),
    ((0, 0, 0), (0.0, 0.0, 0.0)),
    ((128, 128, 0), (60.0, 100.0, 50.19607843137255)),
    ((0, 128, 128), (180.0, 100.0, 50.19607843137255)),
    ((192, 192, 192), (0.0, 0.0, 75.29411764705883)),
]


@pytest.mark.parametrize(("rgb", "hsv"), HSV_CASES)
def test_rgb2hsv(rgb, hsv):
    assert rgb2hsv(rgb) == pytest.approx(hsv)


@pytest.mark.parametrize(("rgb", "hsv"), HSV_CASES)
def test_hsv2rgb(rgb, hsv):
    assert hsv2rgb(hsv) == pytest.approx(rgb)


def test_hsv_matches_colorsys():
    """Cross-check the maths against the standard library."""
    import colorsys

    for rgb in [(255, 0, 0), (10, 20, 205), (128, 128, 0), (7, 3, 1), (250, 251, 252)]:
        h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in rgb])
        assert rgb2hsv(rgb) == pytest.approx((h * 360, s * 100, v * 100))


def test_hsl_hsv_round_trip():
    for hsl in [(0, 100, 50), (120, 50, 25), (240, 0, 100), (37, 63, 81), (0, 0, 0)]:
        assert hsv2hsl(hsl2hsv(hsl)) == pytest.approx(hsl)


def test_hsl2hsv_known_values():
    assert hsl2hsv((0, 100, 50)) == pytest.approx((0.0, 100.0, 100.0))
    assert hsl2hsv((0, 0, 100)) == pytest.approx((0.0, 0.0, 100.0))
    assert hsl2hsv((0, 0, 0)) == pytest.approx((0.0, 0.0, 0.0))


def test_hsv2hsl_known_values():
    assert hsv2hsl((0, 100, 100)) == pytest.approx((0.0, 100.0, 50.0))
    assert hsv2hsl((0, 0, 100)) == pytest.approx((0.0, 0.0, 100.0))
    assert hsv2hsl((0, 0, 0)) == pytest.approx((0.0, 0.0, 0.0))


def test_hsv_hex_and_web():
    assert hsv2hex((0, 100, 100)) == "#f00"
    assert hex2hsv("#f00") == pytest.approx((0.0, 100.0, 100.0))
    assert hex2hsv("#ff0000") == pytest.approx((0.0, 100.0, 100.0))
    assert hsv2web((240, 100, 100)) == "blue"
    assert web2hsv("blue") == pytest.approx((240.0, 100.0, 100.0))
    assert web2hsv("#f00") == pytest.approx((0.0, 100.0, 100.0))


@pytest.mark.parametrize("func", [hsv2hsl, hsv2rgb, hsv2hex, hsv2web])
def test_bad_hsv_input(func):
    for bad in [(361, 0, 0), (0, 101, 0), (0, 0, 101), (0, 0, -1), (0, 0), "a"]:
        with pytest.raises(InvalidColorError):
            func(bad)


def test_bad_input_to_hsv_producers():
    with pytest.raises(InvalidColorError):
        hsl2hsv((361, 0, 0))
    with pytest.raises(InvalidColorError):
        rgb2hsv((256, 0, 0))
    with pytest.raises(InvalidColorError):
        hex2hsv("nope")
    with pytest.raises(InvalidColorError):
        web2hsv("nope")
