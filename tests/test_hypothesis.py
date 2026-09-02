"""Properties explored by Hypothesis rather than by a fixed sample.

This file and ``test_properties.py`` are answers to the same question and they
are not redundant. The sweeps there are aimed: they were built after measuring
that the release which broke ``Color("mintcream")`` failed on 9% of
gamut-surface points and on none of a stride-8 interior grid, so they walk the
surface deliberately. Aiming is what makes them cheap and repeatable, and it is
also their limit -- they only look where the last bug was, and every one of
their samples is an 8-bit integer triple.

Hypothesis covers the other half. It generates float channels, alphas and step
counts, biases towards the boundaries of each range on its own, shrinks a
failure to the smallest input that still fails, and remembers it. The
properties below are mostly ones a fixed sweep cannot state: bounds that hold
to a tolerance the standard implies, and asymmetries that hold in a particular
direction.

Two of these tests assert a *bound* rather than an equality, and neither bound
is a guess -- each was measured first, and each falls out of how many digits
the writer emits.
"""

from hypothesis import assume, given, strategies as st

from colourings import Color, color_scale
from colourings.css import hsla2css
from colourings.definitions import COLOR_NAME_TO_RGB
from colourings.difference import delta_e_cie94
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

SYMMETRIC_METRICS = ["cie76", "ciede2000", "ok"]
ALL_METRICS = [*SYMMETRIC_METRICS, "cie94"]

## In rgb channel units, set where float noise is and not where the eye is.
ROUND_TRIP_TOLERANCE = dict.fromkeys(ROUND_TRIP_SPACES, 1e-9)
## Two are looser by derivation rather than by measurement. Oklch's chroma and
## YUV's U and V pass through ``_threshold``, whose FLOAT_ERROR (5e-7) clamp
## costs at most FLOAT_ERROR x the inverse transform's gain x 255 -- for YUV
## 5e-7 x 1.13983 x 255 = 1.5e-4, against a worst case found of 1.6e-4. 1e-3
## clears both and is still 500 times under a single hex digit.
ROUND_TRIP_TOLERANCE["oklch"] = 1e-3
ROUND_TRIP_TOLERANCE["yuv"] = 1e-3

## Floats rather than the sweeps' 8-bit integers: nothing quantises a channel
## on the way through, so the interesting failures are between them.
channels = st.floats(min_value=0, max_value=255, allow_nan=False, allow_infinity=False)
rgbs = st.tuples(channels, channels, channels)
alphas = st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
named = st.sampled_from(sorted(COLOR_NAME_TO_RGB))
steps = st.integers(min_value=2, max_value=12)
spaces = st.sampled_from(["hsl", "lab", "lch", "oklab", "oklch"])


def _chroma(color: Color) -> float:
    """The chroma of a color in L*a*b*, which is what CIE94 weights by."""
    return float(color.lch[1])


@given(rgbs)
def test_every_output_is_inside_its_documented_range(rgb):
    """The general form of the mintcream bug, over float channels rather than
    the integer triples the sweep uses."""
    color = Color(rgb=rgb)
    for name, predicate in FORMAT_PREDICATES:
        value = getattr(color, name)
        assert predicate(value), f"{name} of rgb{rgb} is {value}"


@given(rgbs)
def test_round_trips_are_exact_to_floating_point(rgb):
    """Stronger than the sweep, which compares ``hex_l`` and so tolerates any
    error under half a channel step. Nine of the eleven spaces return within
    1e-9, so an error of a hundredth of a channel -- invisible in the hex --
    would still fail this. The other two are bounded by the clamp that causes
    them; see ``ROUND_TRIP_TOLERANCE``."""
    color = Color(rgb=rgb)
    for space in ROUND_TRIP_SPACES:
        back = Color(**{space: getattr(color, space)})
        tolerance = ROUND_TRIP_TOLERANCE[space]
        for got, want in zip(back.rgb, color.rgb, strict=True):
            assert abs(got - want) < tolerance, f"{space} of rgb{rgb}: {got} != {want}"


@given(rgbs, alphas)
def test_alpha_is_carried_through_every_space_unchanged(rgb, alpha):
    """No colour space stores alpha, so every conversion has to leave it
    alone."""
    color = Color(rgb=rgb, alpha=alpha)
    for space in ROUND_TRIP_SPACES:
        back = Color(**{space: getattr(color, space)}, alpha=color.alpha)
        assert back.alpha == alpha


@given(rgbs)
def test_text_forms_round_trip_within_a_channel_step(rgb):
    """``hex`` and ``web`` are 8-bit, so they can only be right to half a step
    -- but no worse than that, in either direction."""
    color = Color(rgb=rgb)
    for text in (color.hex_l, color.hex, color.web):
        back = Color(text)
        for got, want in zip(back.rgb, color.rgb, strict=True):
            assert abs(got - want) <= 0.5 + 1e-9, f"{text!r} of rgb{rgb}"


@given(rgbs, rgbs)
def test_contrast_ratio_is_symmetric_and_within_its_bounds(first, second):
    """WCAG's ratio is defined on the lighter and the darker of the pair, so
    which way round it is asked cannot matter. 1 and 21 are the only reachable
    extremes: identical colors, and black against white."""
    a, b = Color(rgb=first), Color(rgb=second)
    ratio = a.contrast_ratio(b)
    assert ratio == b.contrast_ratio(a)
    assert 1.0 <= ratio <= 21.0
    assert a.contrast_ratio(a) == 1.0


@given(rgbs, rgbs)
def test_every_metric_is_zero_on_itself_and_never_negative(first, second):
    a, b = Color(rgb=first), Color(rgb=second)
    for metric in ALL_METRICS:
        assert a.delta_e(a, metric=metric) == 0.0
        assert a.delta_e(b, metric=metric) >= 0.0


@given(rgbs, rgbs)
def test_the_symmetric_metrics_are_symmetric(first, second):
    """CIE76 is a Euclidean distance and Oklab's is too, so those are nearly
    free. CIEDE2000 is the one worth the sweep: it is built to be symmetric,
    and its hue-rotation terms are where that breaks."""
    a, b = Color(rgb=first), Color(rgb=second)
    for metric in SYMMETRIC_METRICS:
        assert a.delta_e(b, metric=metric) == b.delta_e(a, metric=metric)


@given(rgbs, rgbs)
def test_cie94_grows_as_its_reference_loses_chroma(first, second):
    """CIE94's asymmetry has a direction, which is the useful thing to pin.

    Only the weights differ between the two argument orders, and both divide
    by a term increasing in the *reference's* chroma. So the order with the
    duller reference gives the larger distance -- and by a long way: neutral
    grey against magenta is 115.7 where magenta against grey is 19.8.
    """
    a, b = Color(rgb=first), Color(rgb=second)
    assume(abs(_chroma(a) - _chroma(b)) > 1e-6)
    duller, brighter = sorted((a, b), key=_chroma)
    assert delta_e_cie94(duller.lab, brighter.lab) >= delta_e_cie94(
        brighter.lab, duller.lab
    )


## Each form's digit count sets how far a colour can move out and back:
## ``hex`` and ``rgb`` are 8-bit, so half a channel, where ``hsl`` and
## ``oklch`` carry more. Alphas likewise: 1/510 for a byte, 5e-5 for four
## decimal places.
CSS_FORM_TOLERANCES = {
    "hex": (0.5 + 1e-9, 1 / 510 + 1e-9),
    "rgb": (0.5 + 1e-9, 5e-5 + 1e-9),
    "hsl": (0.25, 5e-5 + 1e-9),
    "oklch": (0.25, 5e-5 + 1e-9),
}


@given(rgbs, alphas)
def test_anything_written_as_css_reads_back_as_the_same_colour(rgb, alpha):
    """Whatever ``hsla2css`` writes, ``Color`` reads.

    Not ``css2hsla``, deliberately: that function reads color *functions* and
    says so, and the ``hex`` form is not one. ``Color`` is the entry point
    that accepts every form, so it is the one this property is about.
    """
    color = Color(rgb=rgb, alpha=alpha)
    for form, (channel_tolerance, alpha_tolerance) in CSS_FORM_TOLERANCES.items():
        css = hsla2css(color.hsl, color.alpha, form=form)
        back = Color(css)
        for got, want in zip(back.rgb, color.rgb, strict=True):
            assert abs(got - want) <= channel_tolerance, f"{css!r} of rgb{rgb}"
        assert abs(back.alpha - color.alpha) <= alpha_tolerance, f"{css!r} alpha"


@given(rgbs, rgbs, steps, spaces)
def test_a_scale_has_the_length_and_the_ends_it_was_asked_for(
    first, second, count, space
):
    start, end = Color(rgb=first), Color(rgb=second)
    scale = color_scale((start, end), count, space=space)
    assert len(scale) == count
    assert scale[0] == start
    assert scale[-1] == end


@given(rgbs, alphas, rgbs, alphas, steps)
def test_alpha_crosses_a_scale_monotonically(
    first, start_alpha, second, end_alpha, count
):
    """Nothing quantises alpha, so unlike a channel it keeps any drift it
    picks up -- and above 1.0 ``Color.alpha`` rejects it outright."""
    start = Color(rgb=first, alpha=start_alpha)
    end = Color(rgb=second, alpha=end_alpha)
    scale = color_scale((start, end), count)
    assert scale[0].alpha == start_alpha
    assert scale[-1].alpha == end_alpha
    seen = [c.alpha for c in scale]
    assert all(0.0 <= a <= 1.0 for a in seen)
    assert seen == sorted(seen, reverse=start_alpha > end_alpha)


@given(rgbs, rgbs)
def test_an_opaque_source_hides_whatever_is_behind_it(source, backdrop):
    """Porter-Duff source-over at alpha 1 is the source, whatever the
    backdrop."""
    front, back = Color(rgb=source), Color(rgb=backdrop)
    result = front.blend(back)
    for got, want in zip(result.rgb, front.rgb, strict=True):
        assert abs(got - want) < 1e-9
    assert result.alpha == 1.0


@given(rgbs, rgbs)
def test_a_fully_transparent_source_leaves_the_backdrop_alone(source, backdrop):
    """The other end of source-over, and the end where a wrong divide by the
    composited alpha produces a NaN rather than a wrong colour."""
    front = Color(rgb=source, alpha=0.0)
    back = Color(rgb=backdrop)
    result = front.blend(back)
    for got, want in zip(result.rgb, back.rgb, strict=True):
        assert abs(got - want) < 1e-9


@given(rgbs, alphas)
def test_equal_colours_hash_alike(rgb, alpha):
    """The hash contract, in the direction that matters: equal implies equal
    hashes. The converse is a collision, which is allowed."""
    first = Color(rgb=rgb, alpha=alpha)
    second = Color(rgb=rgb, alpha=alpha)
    assert first == second
    assert hash(first) == hash(second)


@given(named)
def test_a_named_colour_is_its_own_nearest_name(name):
    """Searching the table by distance has to return distance zero for a
    colour that is in the table -- though not necessarily the same *name*:
    ``aqua`` and ``cyan`` are one colour with two entries."""
    color = Color(name)
    for metric in ("ok", "ciede2000", "cie76"):
        nearest = Color(color.nearest_name(metric=metric))
        assert nearest.hex_l == color.hex_l
