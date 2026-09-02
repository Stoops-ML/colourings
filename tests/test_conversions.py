from unittest.mock import patch

import pytest

from colourings.conversions import (
    clear_caches,
    cmyk2rgb,
    contrast_ratio,
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
    in_srgb_gamut,
    lab2lch,
    lab2rgb,
    lab2xyz,
    lch2lab,
    lch2rgb,
    oklab2oklch,
    oklab2rgb,
    oklch2oklab,
    oklch2rgb,
    rgb2cmyk,
    rgb2hex,
    rgb2hsl,
    rgb2hsv,
    rgb2lab,
    rgb2lch,
    rgb2oklab,
    rgb2oklch,
    rgb2relative_luminance,
    rgb2web,
    rgb2xyz,
    rgb2yuv,
    rgba2hsl,
    rgbaf2hsl,
    rgbf2hsl,
    rgbf2rgb,
    web2hex,
    web2hsl,
    web2hsv,
    web2rgb,
    xyz2lab,
    xyz2rgb,
    yuv2rgb,
)
from colourings.definitions import RGB_TO_COLOR_NAMES
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
    with pytest.raises(ValueError, match="Input is not an RGBAf type"):
        rgbaf2hsl("a")  # type: ignore
    with pytest.raises(ValueError, match="Input is not an RGBAf type"):
        rgbaf2hsl((2, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGBAf type"):
        rgbaf2hsl((0, 2, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGBAf type"):
        rgbaf2hsl((0, 0, 2, 0))
    with pytest.raises(ValueError, match="Input is not an RGBAf type"):
        rgbaf2hsl((0, 0, 0, 2))


def test_bad_rgba2hsl():
    with pytest.raises(ValueError, match="Input is not an RGBA type"):
        rgba2hsl("a")  # type: ignore
    with pytest.raises(ValueError, match="Input is not an RGBA type"):
        rgba2hsl((256, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGBA type"):
        rgba2hsl((0, 256, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGBA type"):
        rgba2hsl((0, 0, 256, 0))
    with pytest.raises(ValueError, match="Input is not an RGBA type"):
        rgba2hsl((0, 0, 0, 256))


def test_bad_rgbf2hsl():
    with pytest.raises(ValueError, match="Input is not an RGBf type"):
        rgbf2hsl("a")  # type: ignore
    with pytest.raises(ValueError, match="Input is not an RGBf type"):
        rgbf2hsl((1.1, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGBf type"):
        rgbf2hsl((0, 1.1, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGBf type"):
        rgbf2hsl((0, 0, 1.1, 0))
    with pytest.raises(ValueError, match="Input is not an RGBf type"):
        rgbf2hsl((0, 0, 0, 1.1))


def test_bad_hsla2hsl():
    with pytest.raises(ValueError, match="Input is not an HSLA type"):
        hsla2hsl("a")  # type: ignore
    with pytest.raises(ValueError, match="Input is not an HSLA type"):
        hsla2hsl((370, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not an HSLA type"):
        hsla2hsl((0, 200, 0, 0))
    with pytest.raises(ValueError, match="Input is not an HSLA type"):
        hsla2hsl((0, 0, 200, 0))
    with pytest.raises(ValueError, match="Input is not an HSLA type"):
        hsla2hsl((0, 0, 0, 200))


def test_bad_hex2web():
    with pytest.raises(ValueError, match="Input is not of hex type"):
        hex2web("black")


def test_bad_web2hex():
    ## A malformed hex used to raise AttributeError here, which is neither
    ## accurate nor catchable alongside every other bad-colour error.
    with pytest.raises(InvalidColorError):
        web2hex("#1234")
    with pytest.raises(InvalidColorError):
        web2hex("123")


def test_bad_web2rgb():
    with pytest.raises(ValueError, match="Input is not of web type"):
        web2rgb("#1234")
    with pytest.raises(ValueError, match="Input is not of web type"):
        web2rgb("123")


def test_bad_web2hsl():
    with pytest.raises(ValueError, match="Input is not an web type"):
        web2hsl("#1234")
    with pytest.raises(ValueError, match="Input is not an web type"):
        web2hsl("123")


def test_bad_hsl2web():
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2web("a")  # type: ignore
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2web((0, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2web((361, 0, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2web((0, 110, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2web((0, 0, 110))


def test_bad_hsl2hex():
    with pytest.raises(ValueError, match="Input is not of hsl type"):
        hsl2hex("a")  # type: ignore
    with pytest.raises(ValueError, match="Input is not of hsl type"):
        hsl2hex((0, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not of hsl type"):
        hsl2hex((361, 0, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2web((0, 110, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2web((0, 0, 110))


def test_bad_hex2hsl():
    with pytest.raises(ValueError, match="Input is not of hex type"):
        hex2hsl("black")
    with pytest.raises(ValueError, match="Input is not of hex type"):
        hex2hsl("#black")


def test_bad_rgb2web():
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2web("a")  # type: ignore
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2web((1, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2web((-1, 0, 0))


def test_bad_hsl2rgb():
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2rgb((0, 102, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2rgb((0, 0, 102))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2rgb((0, 0, -1))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2rgb((0, -1, 0))


def test_bad_rgb2hex():
    with pytest.raises(ValueError, match="Input is not of RGB type"):
        rgb2hex((-1, 0, 0, 0))
    with pytest.raises(ValueError, match="Input is not of RGB type"):
        rgb2hex((260, 0, 0))


def test_bad_rgb2hsl():
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2hsl((0, 0, -1))
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2hsl((0, -1, 0))
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2hsl((-1, 0, 0))


def test_bad_hex2rgb():
    with pytest.raises(ValueError, match="Input is not of hex type"):
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
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2hsla((-1, 0, 0), 1)


def test_bad_hsl2hslaf():
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2hslaf((-1, 0, 0), 1)


def test_bad_hslf2hsl():
    with pytest.raises(ValueError, match="Input is not an HSLf type"):
        hslf2hsl((-1, 0, 0))


def test_bad_hsl2hslf():
    with pytest.raises(ValueError, match="Input is not an HSLf type"):
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
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2hsl((300, 0, 0))
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2hsl((300, 0, 0))


def test_unhashable_non_sequence_raises_conversion_error():
    """A set is unhashable and not a sequence: the conversion still rejects it."""
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        rgb2hsl({255, 0, 1})  # type: ignore


def test_rgbf2rgb():
    assert rgbf2rgb((1.0, 0.5, 0.0)) == (255.0, 127.5, 0.0)
    assert rgbf2rgb((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)


def test_bad_hsl2rgbf():
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2rgbf((361, 0, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2rgbf((0, 110, 0))
    with pytest.raises(ValueError, match="Input is not an HSL type"):
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


## Reference values for sRGB primaries under D65, as published for CIE XYZ and
## CIE L*a*b*.
SPACE_REFERENCES = [
    ((255, 255, 255), (95.047, 100.0, 108.883), (100.0, 0.0, 0.0)),
    ((0, 0, 0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ((255, 0, 0), (41.2456, 21.2673, 1.9334), (53.2408, 80.0925, 67.2032)),
    ((0, 255, 0), (35.7576, 71.5152, 11.9192), (87.7347, -86.1827, 83.1793)),
    ((0, 0, 255), (18.0437, 7.2175, 95.0304), (32.2970, 79.1875, -107.8602)),
    ((128, 128, 128), (20.516893, 21.586052, 23.503539), (53.5850, 0.0, 0.0)),
]


@pytest.mark.parametrize(("rgb", "xyz", "lab"), SPACE_REFERENCES)
def test_rgb2xyz_reference_values(rgb, xyz, lab):  # noqa: ARG001
    assert rgb2xyz(rgb) == pytest.approx(xyz, abs=1e-3)


@pytest.mark.parametrize(("rgb", "xyz", "lab"), SPACE_REFERENCES)
def test_rgb2lab_reference_values(rgb, xyz, lab):  # noqa: ARG001
    assert rgb2lab(rgb) == pytest.approx(lab, abs=1e-3)


@pytest.mark.parametrize(("rgb", "xyz", "lab"), SPACE_REFERENCES)
def test_xyz2rgb_and_lab2rgb_invert(rgb, xyz, lab):
    assert xyz2rgb(xyz) == pytest.approx(rgb, abs=1e-2)
    assert lab2rgb(lab) == pytest.approx(rgb, abs=1e-2)


def test_white_is_exactly_l100():
    """The white point is derived from the matrix so this is exact."""
    assert rgb2lab((255, 255, 255)) == (100.0, 0.0, 0.0)


def test_xyz2lab_and_lab2xyz():
    assert xyz2lab((95.047, 100.0, 108.883)) == pytest.approx((100, 0, 0), abs=1e-3)
    assert lab2xyz((100, 0, 0)) == pytest.approx((95.047, 100.0, 108.883), abs=1e-3)


def test_lab2lch_and_lch2lab():
    assert lab2lch((53.2408, 80.0925, 67.2032)) == pytest.approx(
        (53.2408, 104.5518, 39.999), abs=1e-3
    )
    assert lch2lab((53.2408, 104.5518, 39.999)) == pytest.approx(
        (53.2408, 80.0925, 67.2032), abs=1e-3
    )
    ## hue wraps rather than going negative
    assert lab2lch((50, 10, -10)).hue == pytest.approx(315.0)


def test_rgb2lch_reference():
    assert rgb2lch((255, 0, 0)) == pytest.approx((53.2408, 104.5518, 39.999), abs=1e-3)
    assert lch2rgb((53.2408, 104.5518, 39.999)) == pytest.approx((255, 0, 0), abs=1e-2)


CMYK_CASES = [
    ((255, 0, 0), (0.0, 100.0, 100.0, 0.0)),
    ((0, 0, 0), (0.0, 0.0, 0.0, 100.0)),
    ((255, 255, 255), (0.0, 0.0, 0.0, 0.0)),
    ((0, 255, 255), (100.0, 0.0, 0.0, 0.0)),
    ((128, 128, 0), (0.0, 0.0, 100.0, 49.80392156862745)),
]


@pytest.mark.parametrize(("rgb", "cmyk"), CMYK_CASES)
def test_cmyk(rgb, cmyk):
    assert rgb2cmyk(rgb) == pytest.approx(cmyk)
    assert cmyk2rgb(cmyk) == pytest.approx(rgb)


def test_yuv_reference_values():
    assert rgb2yuv((255, 0, 0)) == pytest.approx((0.299, -0.147108, 0.614777), abs=1e-6)
    assert rgb2yuv((0, 0, 0)) == (0.0, 0.0, 0.0)


def test_greys_have_no_chroma_in_yuv():
    """Working from the B-Y and R-Y differences keeps this exact."""
    for level in (0, 64, 128, 192, 255):
        yuv = rgb2yuv((level, level, level))
        assert yuv.u == 0.0
        assert yuv.v == 0.0
        assert yuv.luma == pytest.approx(level / 255)


ROUND_TRIPS = [
    (rgb2xyz, xyz2rgb),
    (rgb2lab, lab2rgb),
    (rgb2lch, lch2rgb),
    (rgb2oklab, oklab2rgb),
    (rgb2cmyk, cmyk2rgb),
    (rgb2yuv, yuv2rgb),
]


@pytest.mark.parametrize(("forward", "backward"), ROUND_TRIPS)
def test_round_trips(forward, backward):
    for rgb in [
        (0, 0, 0),
        (255, 255, 255),
        (255, 0, 0),
        (12, 200, 37),
        (128, 128, 128),
        (7, 3, 1),
        (250, 251, 252),
    ]:
        assert backward(forward(rgb)) == pytest.approx(rgb, abs=1e-6)


def test_out_of_gamut_is_clamped_not_rejected():
    """A LAB value outside sRGB has no encoding, so it clamps."""
    rgb = lab2rgb((100, -128, 127))
    assert all(0 <= c <= 255 for c in rgb)


@pytest.mark.parametrize(
    ("func", "bad"),
    [
        (rgb2xyz, (256, 0, 0)),
        (xyz2rgb, (200, 0, 0)),
        (xyz2lab, (0, 0, 200)),
        (lab2xyz, (101, 0, 0)),
        (lab2lch, (0, -200, 0)),
        (lch2lab, (0, 200, 0)),
        (rgb2cmyk, (256, 0, 0)),
        (cmyk2rgb, (101, 0, 0, 0)),
        (rgb2yuv, (256, 0, 0)),
        (yuv2rgb, (2, 0, 0)),
        (rgb2lab, (256, 0, 0)),
        (rgb2lch, (256, 0, 0)),
        (rgb2oklab, (256, 0, 0)),
        (oklab2rgb, (2, 0, 0)),
        (oklab2oklch, (0, 0.5, 0)),
        (oklch2oklab, (0, 0.5, 0)),
        (rgb2oklch, (256, 0, 0)),
        (oklch2rgb, (0, 0, 400)),
    ],
)
def test_bad_input_rejected(func, bad):
    with pytest.raises(InvalidColorError):
        func(bad)


def test_greys_are_neutral_in_xyz():
    """A grey must be an exact scalar multiple of the white point."""
    from colourings.definitions import D65_WHITE_POINT

    for level in (0, 64, 128, 192, 255):
        xyz = rgb2xyz((level, level, level))
        ratios = [c / w for c, w in zip(xyz, D65_WHITE_POINT, strict=True)]
        assert ratios[0] == pytest.approx(ratios[1]) == pytest.approx(ratios[2])
        assert rgb2lab((level, level, level))[1:] == pytest.approx((0.0, 0.0))


## Reference values published with Oklab (Ottosson, 2020) for the sRGB
## primaries, rounded to five decimal places.
OKLAB_REFERENCE = [
    ((255, 255, 255), (1.0, 0.0, 0.0)),
    ((0, 0, 0), (0.0, 0.0, 0.0)),
    ((255, 0, 0), (0.62796, 0.22486, 0.12585)),
    ((0, 255, 0), (0.86644, -0.23389, 0.17950)),
    ((0, 0, 255), (0.45201, -0.03246, -0.31153)),
]


@pytest.mark.parametrize(("rgb", "oklab"), OKLAB_REFERENCE)
def test_rgb2oklab_reference(rgb, oklab):
    assert rgb2oklab(rgb) == pytest.approx(oklab, abs=1e-5)
    ## The five decimal places the reference is quoted to are worth about
    ## 0.02 of a channel on the way back, so the return leg is looser.
    assert oklab2rgb(oklab) == pytest.approx(rgb, abs=5e-2)


def test_white_is_l1_in_oklab():
    """Off by 6.5e-9, the amount the published matrix's first row is short."""
    lightness, a, b = rgb2oklab((255, 255, 255))
    assert lightness == pytest.approx(1.0, abs=1e-8)
    assert (a, b) == pytest.approx((0.0, 0.0), abs=1e-7)


def test_greys_have_no_hue_in_oklch():
    """A grey keeps its 2e-8 of residual chroma in Oklab, but not in Oklch.

    Clamping it in Oklab would cost 2.6e-5 of a channel on the way back, so it
    is left alone there and resolved where a stray hue would be visible.
    """
    for level in (0, 64, 128, 192, 255):
        assert rgb2oklab((level, level, level))[1:] == pytest.approx(
            (0.0, 0.0), abs=1e-7
        )
        oklch = rgb2oklch((level, level, level))
        assert oklch.chroma == 0.0
        assert oklch.hue == 0.0


def test_oklab2oklch_and_oklch2oklab():
    ## Taken from the full-precision red rather than the rounded reference
    ## above, whose fifth decimal place moves the hue by 1e-3.
    oklab = rgb2oklab((255, 0, 0))
    assert oklab2oklch(oklab) == pytest.approx((0.62796, 0.25768, 29.2339), abs=1e-4)
    assert oklch2oklab(oklab2oklch(oklab)) == pytest.approx(oklab, abs=1e-15)
    ## hue wraps rather than going negative
    assert oklab2oklch((0.5, 0.1, -0.1)).hue == pytest.approx(315.0)


def test_oklab_lightness_is_perceptual():
    """Oklab L of mid grey sits near 0.6, where HSL and CIE L* put it at 0.5."""
    assert rgb2oklab((128, 128, 128)).lightness == pytest.approx(0.5999, abs=1e-4)


def test_every_named_colour_round_trips_through_oklab():
    worst = 0.0
    for rgb in RGB_TO_COLOR_NAMES:
        back = oklab2rgb(rgb2oklab(rgb))
        worst = max(worst, max(abs(a - b) for a, b in zip(rgb, back, strict=True)))
    assert worst < 1e-11


def test_oklch_round_trip_pays_for_neutral_greys():
    """Oklch is exact except on a grey, whose hue it discards on the way out.

    That is the deliberate trade made in oklab2oklch: 2.6e-5 of a channel,
    which no output format can represent, buys a grey with no phantom hue.
    """
    worst_grey, worst_colour = 0.0, 0.0
    for rgb in RGB_TO_COLOR_NAMES:
        back = oklch2rgb(rgb2oklch(rgb))
        error = max(abs(a - b) for a, b in zip(rgb, back, strict=True))
        if len(set(rgb)) == 1:
            worst_grey = max(worst_grey, error)
        else:
            worst_colour = max(worst_colour, error)
    assert worst_colour < 1e-11
    assert worst_grey < 1e-4


@pytest.mark.parametrize(
    ("space", "to_space"),
    [
        ("lab", rgb2lab),
        ("lch", rgb2lch),
        ("oklab", rgb2oklab),
        ("oklch", rgb2oklch),
        ("xyz", rgb2xyz),
        ("yuv", rgb2yuv),
    ],
)
def test_in_srgb_gamut_accepts_every_colour_srgb_can_show(space, to_space):
    """Anything reached from an sRGB colour is by definition inside the gamut.

    This is the assertion that matters, because the failure that would make the
    predicate useless is a false negative on an ordinary colour."""
    for red in range(0, 256, 15):
        for green in range(0, 256, 15):
            for blue in range(0, 256, 15):
                value = to_space((red, green, blue))
                assert in_srgb_gamut(value, space), (space, value)


@pytest.mark.parametrize(
    ("space", "value"),
    [
        ("lab", (100, 120, -120)),
        ("lab", (50, 100, 0)),
        ("lch", (50, 120, 0)),
        ("oklab", (0.9, 0.3, -0.3)),
        ("oklch", (0.9, 0.35, 200)),
        ("xyz", (0, 0, 110)),
        ("yuv", (1.0, 0.436, 0.615)),
    ],
)
def test_in_srgb_gamut_rejects_colours_srgb_cannot_show(space, value):
    assert not in_srgb_gamut(value, space)


@pytest.mark.parametrize(
    ("space", "inside", "outside"),
    [
        ## The wide-gamut spaces CSS's color() names. Each has a redder red
        ## than sRGB can show, which is what makes it wide.
        ("display-p3", (0.4, 0.5, 0.6), (1.0, 0.0, 0.0)),
        ("a98-rgb", (0.4, 0.5, 0.6), (1.0, 0.0, 0.0)),
        ("rec2020", (0.4, 0.5, 0.6), (1.0, 0.0, 0.0)),
        ## CSS's XYZ, with Y of 1 for white where `xyz` here uses 100.
        ("xyz-d65", (0.9504559270516716, 1.0, 1.0890577507598784), (0.0, 0.0, 1.1)),
    ],
)
def test_in_srgb_gamut_answers_for_the_css_color_function_spaces(
    space, inside, outside
):
    """The question `color()` makes a caller want to ask. A wide-gamut value
    is converted and clipped, and nothing in the resulting `Color` records
    that -- so it has to be asked before converting."""
    assert in_srgb_gamut(inside, space)
    assert not in_srgb_gamut(outside, space)


@pytest.mark.parametrize("space", ["display-p3", "a98-rgb", "rec2020", "xyz-d65"])
@pytest.mark.parametrize("value", [(0.5, 0.5), (0.5, 0.5, 0.5, 0.5), ()])
def test_in_srgb_gamut_refuses_the_wrong_number_of_components(space, value):
    """CSS allows components outside [0, 1] in these spaces, so the length is
    the only thing left to check -- and it is still worth checking."""
    with pytest.raises(InvalidColorError, match="Input is not"):
        in_srgb_gamut(value, space)


def test_in_srgb_gamut_agrees_with_what_the_conversion_does():
    """The predicate has to answer the question it is asked: was this clipped."""
    for lightness in range(0, 101, 10):
        for a in range(-128, 128, 16):
            for b in range(-128, 128, 16):
                value = (lightness, a, b)
                clipped = lab2rgb(value)
                ## A clipped colour is one that hit a channel limit. Only to
                ## within float error: `1.055 * 1.0 - 0.055` is
                ## 0.9999999999999999, so a channel pinned to the top comes
                ## back as 254.99999999999997 rather than 255.0.
                pinned = any(c < 1e-9 or c > 255.0 - 1e-9 for c in clipped)
                if not in_srgb_gamut(value, space="lab", tolerance=2.0):
                    assert pinned, value


def test_in_srgb_gamut_tolerance_is_in_eight_bit_levels():
    """A primary written to three decimal places falls outside sRGB.

    Not a flaw in the test: the gamut boundary passes exactly through every
    saturated colour, so rounding one at all moves it off the surface, and
    outwards half the time. The default tolerance covers the rounding that
    cannot be seen once rendered, and no more."""
    exact = rgb2oklab((255, 0, 0))
    assert in_srgb_gamut(exact, "oklab", tolerance=0)
    rounded = tuple(round(v, 3) for v in exact)
    assert not in_srgb_gamut(rounded, "oklab")
    assert in_srgb_gamut(rounded, "oklab", tolerance=10)


def test_in_srgb_gamut_rejects_a_space_that_cannot_leave_the_gamut():
    for space in ("rgb", "hsl", "hsv", "cmyk", "hex", "web", "nonsense"):
        with pytest.raises(ValueError, match="Cannot ask about the gamut"):
            in_srgb_gamut((0, 0, 0), space)


@pytest.mark.parametrize(
    ("space", "value"),
    [
        ("lab", (200, 0, 0)),
        ("oklab", (2, 0, 0)),
        ("xyz", (0, 0, 200)),
        ("yuv", (2, 0, 0)),
        ("lch", (200, 0, 0)),
        ("oklch", (2, 0, 0)),
    ],
)
def test_in_srgb_gamut_rejects_a_malformed_value(space, value):
    """Out of the format's own range is a different error from out of gamut."""
    with pytest.raises(InvalidColorError):
        in_srgb_gamut(value, space)


def test_rgb2relative_luminance_anchors():
    """The primaries must come back as exactly their own coefficients.

    That is what says the channels were linearised before being weighted: a
    primary is 1.0 linear in one channel and 0.0 in the others, so nothing but
    the coefficient survives. Getting anything else back means the transfer
    function was skipped, which is the bug `Color.luminance` embodies."""
    assert rgb2relative_luminance((255, 255, 255)) == 1.0
    assert rgb2relative_luminance((0, 0, 0)) == 0.0
    assert rgb2relative_luminance((255, 0, 0)) == 0.2126
    assert rgb2relative_luminance((0, 255, 0)) == 0.7152
    assert rgb2relative_luminance((0, 0, 255)) == 0.0722


def test_rgb2relative_luminance_is_monotonic_and_bounded():
    previous = -1.0
    for value in range(256):
        luminance = rgb2relative_luminance((value, value, value))
        assert 0.0 <= luminance <= 1.0
        assert luminance > previous
        previous = luminance


def test_rgb2relative_luminance_rejects_a_malformed_value():
    with pytest.raises(InvalidColorError, match="Input is not an RGB type"):
        rgb2relative_luminance((256, 0, 0))


def test_contrast_ratio_anchors():
    assert contrast_ratio((0, 0, 0), (255, 255, 255)) == 21.0
    assert contrast_ratio((255, 0, 0), (255, 0, 0)) == 1.0


def test_contrast_ratio_is_symmetric():
    for other in ((255, 255, 255), (128, 128, 128), (0, 0, 255)):
        assert contrast_ratio((0, 0, 0), other) == contrast_ratio(other, (0, 0, 0))


@pytest.mark.parametrize(
    ("rgb", "expected"),
    [
        ((0x76, 0x76, 0x76), 4.54),
        ((0xFF, 0x00, 0x00), 4.00),
        ((0x00, 0x00, 0xFF), 8.59),
        ((0x59, 0x59, 0x59), 7.00),
        ((0x94, 0x94, 0x94), 3.03),
    ],
)
def test_contrast_ratio_matches_published_values_against_white(rgb, expected):
    """Values quoted widely for these colours on white, to two decimals."""
    assert contrast_ratio(rgb, (255, 255, 255)) == pytest.approx(expected, abs=0.01)


def test_contrast_ratio_stays_within_its_range():
    values = range(0, 256, 51)
    for r in values:
        for g in values:
            for b in values:
                ratio = contrast_ratio((r, g, b), (255, 255, 255))
                assert 1.0 <= ratio <= 21.0
