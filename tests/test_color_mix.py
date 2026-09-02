"""``color-mix()``, from CSS Color 5 section 3.

The tests state consequences of the published algorithm -- the percentage
normalization from CSS Values 5, the fold from CSS Color 5, the premultiplied
interpolation from CSS Color 4 section 13.3, and the hue arcs from its section
13.5 -- rather than recording what this implementation returns.

Two of the specification's own worked examples are checked directly. Its third,
the oklch hue midpoint, cannot be: `oklch(0.7 0.195 60)` is outside the sRGB
gamut, so a package that stores HSL clips it and the published hue is not
reachable through `Color`. The arithmetic that produces it is checked instead,
on `_shift_hue_for_arc`, where the gamut has no say.
"""

import pytest

from colourings import Color, color_scale
from colourings.colour import _shift_hue_for_arc, color_mix2hsla
from colourings.css import (
    is_color_mix,
    normalize_mix_percentages,
    read_mix_item,
    read_mix_method,
)
from colourings.errors import InvalidColorError

MIX_SPACES = ["hsl", "lab", "lch", "oklab", "oklch"]


## --- the specification's own worked examples --------------------------------


def test_the_documented_lch_mix_matches_the_specification():
    """CSS Color 5 section 3.2 states that a half-and-half mix of purple and
    plum in lch is rgb(68.51% 36.01% 68.29%)."""
    mixed = Color("color-mix(in lch, purple, plum)")
    for got, want in zip(mixed.rgb, (68.51, 36.01, 68.29), strict=True):
        assert got / 255 * 100 == pytest.approx(want, abs=0.05)


@pytest.mark.parametrize(
    ("method", "start", "end", "midpoint"),
    [
        ## The specification's own worked example.
        ("shorter", 30.0, 90.0, 60.0),
        ("longer", 30.0, 90.0, 240.0),
        ## And each remaining branch, so that none is only ever skipped: the
        ## shorter arc wrapping over 0 in both directions, the longer arc for
        ## a falling hue, and a pair that needs no adjustment at all.
        ("shorter", 350.0, 10.0, 0.0),
        ("shorter", 10.0, 350.0, 0.0),
        ("longer", 90.0, 30.0, 240.0),
        ("shorter", 0.0, 180.0, 90.0),
    ],
)
def test_the_documented_hue_arcs_match_the_specification(method, start, end, midpoint):
    """CSS Color 4 section 13.5: interpolating hue 30 to hue 90 passes through
    60 the short way and 240 the long way. Exact, not approximate."""
    first, second = [0.6, 0.24, start], [0.8, 0.15, end]
    _shift_hue_for_arc(first, second, 2, method)
    assert (first[2] + second[2]) / 2 % 360.0 == midpoint


def test_mixing_two_transparent_colours_leaves_nothing_to_divide_by():
    """Un-premultiplying divides by the mixed alpha, and here there is none.
    The channels stay where premultiplying left them, at zero, and the result
    is transparent rather than a NaN."""
    mixed = Color("color-mix(in oklab, transparent, transparent)")
    assert mixed.alpha == 0.0
    assert all(channel == channel for channel in mixed.rgb)


def test_a_closing_parenthesis_with_nothing_open_is_reported():
    """The other side of the balance check: too many closers, not too few."""
    with pytest.raises(InvalidColorError, match="Unbalanced parentheses"):
        color_mix2hsla("color-mix(red), blue)")


@pytest.mark.parametrize(
    ("written", "weights", "leftover"),
    [
        ([50.0, 50.0], [50.0, 50.0], 0.0),
        ([50.0, None], [50.0, 50.0], 0.0),
        ([None, 50.0], [50.0, 50.0], 0.0),
        ([None, None], [50.0, 50.0], 0.0),
        ([80.0, 80.0], [50.0, 50.0], 0.0),
        ([30.0, 30.0], [50.0, 50.0], 40.0),
        ([None], [100.0], 0.0),
        ([0.0, 0.0], [0.0, 0.0], 100.0),
    ],
)
def test_percentage_normalization_matches_the_specification(written, weights, leftover):
    """Every form CSS Color 5 section 3.2 lists as equivalent, plus the two
    edges. The first five all mean a half-and-half mix; the sixth means the
    same mix at alpha 0.6, which is what the leftover rule is for."""
    got_weights, got_leftover = normalize_mix_percentages(written)
    assert got_weights == pytest.approx(weights)
    assert got_leftover == pytest.approx(leftover)


def test_a_shortfall_becomes_transparency_rather_than_a_different_colour():
    """The consequence of the leftover rule, through the public API: 30/30 and
    80/80 are the same colour, and only one of them is opaque."""
    thirty = Color("color-mix(in lch, purple 30%, plum 30%)")
    eighty = Color("color-mix(in lch, purple 80%, plum 80%)")
    assert thirty.hex_l == eighty.hex_l
    assert thirty.alpha == pytest.approx(0.6)
    assert eighty.alpha == 1.0


## --- interpolation ----------------------------------------------------------


def test_mixing_with_transparent_does_not_darken():
    """The reason this does not call color_scale.

    CSS Color 4 section 13.3 premultiplies by alpha before interpolating, so
    mixing red with `transparent` gives red at half alpha. Interpolating the
    channels unweighted instead walks them halfway to black, because
    `transparent` is a transparent *black* -- a visibly different answer, not
    a rounding one.
    """
    mixed = Color("color-mix(in oklab, red, transparent)")
    assert mixed.hex_l == Color("red").hex_l
    assert mixed.alpha == pytest.approx(0.5)

    unpremultiplied = color_scale(
        (Color("red"), Color("transparent")), 3, space="oklab"
    )
    assert unpremultiplied[1].hex_l != mixed.hex_l


@pytest.mark.parametrize("space", MIX_SPACES)
@pytest.mark.parametrize("name", ["red", "#3d7ab8", "white", "black", "gray"])
def test_mixing_a_colour_with_itself_returns_it(space, name):
    """Whatever the space and whatever the weights, there is nothing to move
    towards."""
    assert Color(f"color-mix(in {space}, {name}, {name})") == Color(name)
    assert Color(f"color-mix(in {space}, {name} 20%, {name} 80%)") == Color(name)


@pytest.mark.parametrize("space", MIX_SPACES)
def test_a_full_share_of_one_colour_is_that_colour(space):
    assert Color(f"color-mix(in {space}, red 100%, blue 0%)") == Color("red")
    assert Color(f"color-mix(in {space}, red 0%, blue 100%)") == Color("blue")


def test_the_default_space_is_oklab():
    """CSS Color 5 section 3.1: with no interpolation method, assume Oklab."""
    assert Color("color-mix(red, blue)") == Color("color-mix(in oklab, red, blue)")


def test_the_order_of_a_colour_and_its_percentage_does_not_matter():
    """The grammar joins them with `&&`, so either way round is legal."""
    assert Color("color-mix(in oklab, 30% red, blue)") == Color(
        "color-mix(in oklab, red 30%, blue)"
    )


def test_swapping_the_operands_and_their_shares_gives_the_same_colour():
    assert Color("color-mix(in oklab, red 30%, blue 70%)") == Color(
        "color-mix(in oklab, blue 70%, red 30%)"
    )


def test_an_even_three_way_mix_is_the_mix_of_a_mix():
    """The fold weights each merged item by the share the pair carried, so
    three equal parts must come out the same as combining two and then adding
    the third at a third."""
    three = Color("color-mix(in oklab, red, lime, blue)")
    folded = Color(
        "color-mix(in oklab, color-mix(in oklab, red, lime) 66.6667%, blue 33.3333%)"
    )
    assert three.hex_l == folded.hex_l


def test_a_mix_may_contain_a_function_and_another_mix():
    """The arguments nest, which is why they cannot be split on commas."""
    assert Color("color-mix(in oklab, rgb(255 0 0), blue)") == Color(
        "color-mix(in oklab, red, blue)"
    )
    nested = Color("color-mix(in oklab, red, color-mix(in oklab, blue, blue))")
    assert nested == Color("color-mix(in oklab, red, blue)")


def test_the_longer_arc_goes_the_other_way_round_the_wheel():
    """Red to blue is violet the short way and green the long way, which is
    the whole point of the option."""
    shorter = Color("color-mix(in oklch, red, blue)")
    longer = Color("color-mix(in oklch longer hue, red, blue)")
    assert shorter.hex_l != longer.hex_l
    assert longer.green > longer.red
    assert longer.green > longer.blue


## --- what it refuses --------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("color-mix(in srgb, red, blue)", "Cannot interpolate in 'srgb'"),
        ("color-mix(in xyz, red, blue)", "Cannot interpolate in 'xyz'"),
        (
            "color-mix(in oklch increasing hue, red, blue)",
            "Cannot interpolate hue by 'increasing'",
        ),
        ("color-mix(in oklab)", "needs at least one color"),
        ("color-mix()", "needs at least one color"),
        ("color-mix(in oklab, red 150%, blue)", "must be between 0% and 100%"),
        ("color-mix(in oklab, red -10%, blue)", "must be between 0% and 100%"),
        ("color-mix(in oklab, red blue)", "is not one color"),
        ("color-mix(in oklab, red 10% 20%)", "is not one color"),
        ("color-mix(in nonsense hue, red, blue)", "color interpolation method"),
    ],
)
def test_a_mix_that_cannot_be_read_says_why(text, message):
    """`is_color_mix` matches on shape, so a malformed one reaches the parser
    and gets a specific complaint rather than "cannot identify color"."""
    assert is_color_mix(text)
    with pytest.raises(InvalidColorError, match=message):
        Color(text)


def test_unbalanced_parentheses_are_reported_as_such():
    with pytest.raises(InvalidColorError, match="Unbalanced parentheses"):
        ## The inner function is never closed, so the outer `)` closes it and
        ## the arguments are left one level deep.
        color_mix2hsla("color-mix(in oklab, rgb(255 0 0, blue)")


def test_color_mix2hsla_refuses_something_that_is_not_one():
    """Reachable only by calling it directly; `Color` routes by shape first."""
    with pytest.raises(InvalidColorError, match="Not a color-mix"):
        color_mix2hsla("rgb(255 0 0)")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("color-mix(in oklab, red, blue)", True),
        ("COLOR-MIX(IN OKLAB, RED, BLUE)", True),
        ("  color-mix(red, blue)  ", True),
        ("color-mixture(red, blue)", False),
        ("rgb(255 0 0)", False),
        ("red", False),
        ("#ff0000", False),
        (None, False),
        (("color-mix", "red"), False),
    ],
)
def test_is_color_mix_matches_only_that_function(value, expected):
    assert is_color_mix(value) is expected


## --- the pieces, where the whole cannot reach them --------------------------


def test_an_interpolation_method_is_told_from_a_colour_by_its_first_word():
    """The method is optional and shares its position with a colour, so `in`
    is what distinguishes them."""
    assert read_mix_method("in oklab") == ("oklab", "shorter")
    assert read_mix_method("in oklch longer hue") == ("oklch", "longer")
    assert read_mix_method("red") is None
    assert read_mix_method("rgb(255 0 0)") is None


def test_a_mix_item_keeps_the_colour_as_written():
    assert read_mix_item("red 40%") == ("red", 40.0)
    assert read_mix_item("40% red") == ("red", 40.0)
    assert read_mix_item("red") == ("red", None)
    assert read_mix_item("rgb(255 0 0 / 50%) 40%") == ("rgb(255 0 0 / 50%)", 40.0)


def test_a_mix_of_nothing_but_zeroes_is_fully_transparent():
    """Both shares at 0% leaves the whole 100% over, so the alpha multiplier
    is zero -- and the fold has no ratio to interpolate at, which the
    specification says to treat as an even mix."""
    mixed = Color("color-mix(in oklab, red 0%, blue 0%)")
    assert mixed.alpha == 0.0
