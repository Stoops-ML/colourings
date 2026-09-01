"""Properties that must hold for every colour, not just the ones with a test.

Line coverage was 100% while ``Color("mintcream")`` raised, because coverage
proves a line ran, not that what it produced was valid. These tests assert
properties over the input space instead.

Where they look matters more than how many samples they take. Sweeping the
release that broke ``mintcream``, 35172 of 16777216 RGB triples produced an
out-of-range HSL. That is 0.21% overall, but every one of them had a channel
at 0 or 255: a stride-8 interior grid finds none, while 9% of gamut-surface
points fail. Uniform random sampling reaches a surface point about 2.3% of
the time, so it would need a few hundred draws to be confident of one hit.
These tests sweep the surface directly, keep a coarse interior grid as a
guard against anything that is not a boundary case, and add every named
colour so the original regression is covered by name.

Each test walks the sample once and checks every format for that colour,
rather than being parametrised per format and rebuilding the sample each
time. That is the difference between this file taking seconds and taking
minutes.
"""

import pytest

from colourings import Color, color_scale
from colourings.definitions import COLOR_NAME_TO_RGB
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


def gamut_surface(step: int) -> list[tuple[float, float, float]]:
    """RGB triples with at least one channel at an extreme of its range."""
    out: set[tuple[float, float, float]] = set()
    axis = range(0, 256, step)
    for pinned in (0, 255):
        for a in axis:
            for b in axis:
                out.update({(pinned, a, b), (a, pinned, b), (a, b, pinned)})
    return sorted(out)


def interior_grid(step: int) -> list[tuple[float, float, float]]:
    """A coarse grid through the middle of the cube."""
    axis = range(step // 2, 256, step)
    return [(r, g, b) for r in axis for g in axis for b in axis]


NAMED = sorted(tuple(rgb) for rgb in COLOR_NAME_TO_RGB.values())
SAMPLE = sorted(set(gamut_surface(8) + interior_grid(32) + NAMED))

## Every format a Color exposes, with the predicate that defines its range.
FORMAT_PREDICATES = [
    ("hsl", is_hsl),
    ("hsv", is_hsv),
    ("rgb", is_rgb),
    ("rgbf", is_rgbf),
    ("rgba", is_rgba),
    ("rgbaf", is_rgbaf),
    ("hsla", is_hsla),
    ("hslf", is_hslf),
    ("hslaf", is_hslaf),
    ("xyz", is_xyz),
    ("lab", is_lab),
    ("lch", is_lch),
    ("oklab", is_oklab),
    ("oklch", is_oklch),
    ("cmyk", is_cmyk),
    ("yuv", is_yuv),
]

## The subset a Color can also be built from, so they can round-trip.
ROUND_TRIP_SPACES = [
    "hsl",
    "hsv",
    "rgb",
    "rgbf",
    "xyz",
    "lab",
    "lch",
    "oklab",
    "oklch",
    "cmyk",
    "yuv",
]


def test_the_sample_looks_where_the_failures_were():
    """Guard the guard, so a later tweak cannot quietly stop testing anything."""
    assert len(SAMPLE) > 5000
    surface = [rgb for rgb in SAMPLE if any(c in (0, 255) for c in rgb)]
    assert len(surface) > 4000
    assert (245.0, 255.0, 250.0) in SAMPLE  # mintcream, which v1.0.0 rejected
    assert len(NAMED) > 100


def test_every_colour_is_constructible():
    """``Color("mintcream")`` raising was this property failing."""
    for rgb in SAMPLE:
        Color(rgb=rgb)


def test_every_output_is_inside_its_documented_range():
    """The general form of the mintcream bug: a conversion producing a value
    that the library's own validator for that format rejects."""
    for rgb in SAMPLE:
        color = Color(rgb=rgb)
        for name, predicate in FORMAT_PREDICATES:
            value = getattr(color, name)
            assert predicate(value), f"{name} of rgb{rgb} is {value}"


def test_every_rgb_round_trips_through_every_space():
    for rgb in SAMPLE:
        color = Color(rgb=rgb)
        for space in ROUND_TRIP_SPACES:
            back = Color(**{space: getattr(color, space)})
            assert back.hex_l == color.hex_l, f"{space} of rgb{rgb}"


def test_every_rgb_round_trips_through_text_forms():
    for rgb in SAMPLE:
        color = Color(rgb=rgb)
        assert Color(color.hex_l).hex_l == color.hex_l
        assert Color(color.hex).hex_l == color.hex_l
        assert Color(web=color.web).hex_l == color.hex_l


def test_rgb_survives_the_trip_through_hsl():
    """Color stores HSL, so every channel must come back where it started."""
    for rgb in SAMPLE:
        assert Color(rgb=rgb).rgb == pytest.approx(rgb, abs=1e-9)


def test_scales_keep_their_endpoints_and_length():
    """Whatever the two stops and whatever the space, a scale starts and ends
    on them and is as long as it was asked for."""
    stops = [Color(rgb=rgb) for rgb in SAMPLE[::97]]
    assert len(stops) > 50
    for space in ("hsl", "lab", "lch", "oklab", "oklch"):
        for start, end in zip(stops, stops[1:], strict=False):
            for steps in (2, 3, 7):
                scale = color_scale((start, end), steps, space=space)
                assert len(scale) == steps
                assert scale[0] == start
                assert scale[-1] == end
