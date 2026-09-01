import copy
import math
import sys
from unittest.mock import MagicMock, patch

import pytest

from colourings.colour import (
    HEX,
    HSL,
    RGB,
    Color,
    Colour,
    HSL_equivalence,
    RGB_color_picker,
    RGB_equivalence,
    color_scale,
    colour_scale,
    hash_or_str,
    identify_color,
    make_color_factory,
)
from colourings.conversions import hsl2rgb
from colourings.errors import (
    AmbiguousColorError,
    ColorError,
    InvalidColorError,
    UnknownColorError,
)


@patch("tkinter.Tk")
def test_preview(mock_tk):
    c = Colour("red")
    x, y = 300, 300
    mock_root = MagicMock()
    mock_tk.return_value = mock_root
    c.preview(x, y)
    mock_tk.assert_called_once()
    mock_root.geometry.assert_called_once_with(f"{x}x{y}")
    mock_root.config.assert_called_once_with(background=c.hex_l)
    mock_root.title.assert_called_once_with(f"{str(c)} preview")
    mock_root.mainloop.assert_called_once()


def test_preview_without_tkinter():
    """The one import that can be missing must say which package supplies it.

    Setting the entry to None makes ``import tkinter`` raise, which is what a
    minimal Linux install without python3-tkinter looks like from in here.
    """
    c = Colour("red")
    with (
        patch.dict(sys.modules, {"tkinter": None}),
        pytest.raises(ImportError, match="python3-tkinter") as excinfo,
    ):
        c.preview()
    assert "python3-tk" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None


def test_preview_invalid_size_x():
    c = Colour("red")
    with pytest.raises(TypeError, match="`size_x` must be of integer or float type"):
        c.preview("invalid", 300)  # type: ignore


def test_preview_invalid_size_y():
    c = Colour("red")
    with pytest.raises(TypeError, match="`size_y` must be of integer or float type"):
        c.preview(300, "invalid")  # type: ignore


@patch("warnings.warn")
def test_preview_alpha_warning(mock_warn):
    c = Colour("red", alpha=0.5)
    with patch("tkinter.Tk"):
        c.preview(300, 300)
    mock_warn.assert_called_once_with(
        f"Alpha set to {c.alpha}, but is not displayed in the window.",
        stacklevel=2,
    )


def test_bad_colour_scale():
    with pytest.raises(ValueError):
        colour_scale((Color("white"),), 2)


def test_colour_scale_with_exact_inputs():
    assert colour_scale((Color("white"), Color("black")), 2) == [
        Color("white"),
        Color("black"),
    ]
    assert colour_scale((Color("blue"), Color("black")), 2) == [
        Color("blue"),
        Color("black"),
    ]
    assert colour_scale((Color("blue"), Color("black"), Color("blue")), 3) == [
        Color("blue"),
        Color("black"),
        Color("blue"),
    ]
    assert colour_scale(
        (Color("blue"), Color("black"), Color("blue"), Color("orange")), 4
    ) == [
        Color("blue"),
        Color("black"),
        Color("blue"),
        Color("orange"),
    ]
    assert colour_scale(
        (Color("blue"), Color("black"), Color("blue"), Color("orange"), Color("green")),
        5,
    ) == [Color("blue"), Color("black"), Color("blue"), Color("orange"), Color("green")]


def test_colour_scale_with_fewer_inputs():
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors.",
    ):
        colour_scale((Color("white"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors.",
    ):
        colour_scale((Color("blue"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors.",
    ):
        colour_scale((Color("blue"), Color("black"), Color("blue")), 2)


def test_color_scale_with_fewer_inputs():
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors.",
    ):
        color_scale((Color("white"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors.",
    ):
        color_scale((Color("blue"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors.",
    ):
        color_scale((Color("blue"), Color("black"), Color("blue")), 2)


def test_bad_color_change_HSL():
    c = Color("red")
    with pytest.raises(TypeError, match="Value is not a valid HSL"):
        c.lightness = 200
    with pytest.raises(TypeError, match="Value is not a valid HSL"):
        c.lightness = -0.5
    with pytest.raises(TypeError, match="Value is not a valid HSL"):
        c.saturation = 200
    with pytest.raises(TypeError, match="Value is not a valid HSL"):
        c.saturation = -0.5
    with pytest.raises(TypeError, match="Value is not a valid HSL"):
        c.hue = 361
    with pytest.raises(TypeError, match="Value is not a valid HSL"):
        c.hue = -0.5


def test_bad_color_change_alpha():
    c = Color("red")
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1."):
        c.alpha = 2
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1."):
        c.alpha = -0.5


def test_bad_color_change_rgb():
    c = Color("red")
    with pytest.raises(ValueError, match="Input is not an RGB type."):
        c.red = 300
    with pytest.raises(ValueError, match="Input is not an RGB type."):
        c.red = -0.5
    with pytest.raises(ValueError, match="Input is not an RGB type."):
        c.green = 300
    with pytest.raises(ValueError, match="Input is not an RGB type."):
        c.green = -0.5
    with pytest.raises(ValueError, match="Input is not an RGB type."):
        c.blue = 300
    with pytest.raises(ValueError, match="Input is not an RGB type."):
        c.blue = -0.5


def test_bad_color_scale():
    with pytest.raises(ValueError):
        color_scale((Color("white"),), 2)


def test_color_scale_with_exact_inputs():
    assert color_scale((Color("white"), Color("black")), 2) == [
        Color("white"),
        Color("black"),
    ]
    assert color_scale((Color("blue"), Color("black")), 2) == [
        Color("blue"),
        Color("black"),
    ]
    assert color_scale((Color("blue"), Color("black"), Color("blue")), 3) == [
        Color("blue"),
        Color("black"),
        Color("blue"),
    ]
    assert color_scale(
        (Color("blue"), Color("black"), Color("blue"), Color("orange")), 4
    ) == [
        Color("blue"),
        Color("black"),
        Color("blue"),
        Color("orange"),
    ]
    assert color_scale(
        (Color("blue"), Color("black"), Color("blue"), Color("orange"), Color("green")),
        5,
    ) == [Color("blue"), Color("black"), Color("blue"), Color("orange"), Color("green")]


def test_color_scale_interpolates_alpha():
    scale = color_scale([Color("red", alpha=1.0), Color("blue", alpha=0.0)], 5)
    assert [c.alpha for c in scale] == [1.0, 0.75, 0.5, 0.25, 0.0]


def test_color_scale_keeps_the_endpoint_alphas_exactly():
    """An endpoint's alpha is copied, not approximated.

    Interpolating to 1.0000000000000002 would not merely be inexact, it would
    raise: ``Color.alpha`` range-checks without float tolerance."""
    start, end = Color(rgba=(255, 0, 0, 9)), Color("blue", alpha=1.0)
    for steps in (2, 3, 5, 7, 9, 100):
        scale = color_scale([start, end], steps)
        assert scale[0].alpha == start.alpha
        assert scale[-1].alpha == end.alpha
        assert all(0 <= c.alpha <= 1 for c in scale)


def test_color_scale_interpolates_alpha_per_section():
    scale = color_scale(
        [Color("red", alpha=0.0), Color("lime", alpha=1.0), Color("blue", alpha=0.5)],
        5,
    )
    assert [c.alpha for c in scale] == [0.0, 0.5, 1.0, 0.75, 0.5]


@pytest.mark.parametrize("space", ["hsl", "lab", "lch", "oklab", "oklch"])
def test_color_scale_alpha_does_not_depend_on_the_space(space):
    """Alpha belongs to no colour space, so it interpolates the same in each."""
    scale = color_scale(
        [Color("red", alpha=0.2), Color("blue", alpha=0.8)], 3, space=space
    )
    assert [c.alpha for c in scale] == [0.2, 0.5, 0.8]


def test_color_scale_leaves_opaque_colors_opaque():
    scale = color_scale([Color("red"), Color("blue")], 5)
    assert [c.alpha for c in scale] == [1.0] * 5
    assert [c.hex_l for c in scale] == [
        "#ff0000",
        "#ff007f",
        "#ff00ff",
        "#7f00ff",
        "#0000ff",
    ]


def test_range_to_interpolates_alpha():
    scale = list(Color("red", alpha=0.0).range_to(Color("blue", alpha=1.0), 5))
    assert [c.alpha for c in scale] == [0.0, 0.25, 0.5, 0.75, 1.0]


def test_bad_alpha():
    with pytest.raises(ValueError):
        Color(rgb=(1, 1, 1), alpha=-1)
    with pytest.raises(ValueError):
        Color(rgb=(1, 1, 1), alpha=1.1)
    with pytest.raises(ValueError):
        Color(rgba=(1, 1, 1, 1), alpha=0)
    with pytest.raises(ValueError):
        Color(rgba=(1, 1, 1, 1), alpha=1)
    with pytest.raises(ValueError):
        Color(rgbaf=(1, 1, 1, 1), alpha=0)
    with pytest.raises(ValueError):
        Color(hsla=(1, 1, 1, 1), alpha=0)
    with pytest.raises(ValueError):
        Color(hslaf=(1, 1, 1, 1), alpha=0)


ALPHA_CARRYING = [
    ("rgba", (1, 1, 1, 255)),
    ("rgbaf", (1, 1, 1, 1)),
    ("hsla", (1, 1, 1, 100)),
    ("hslaf", (0, 0, 0, 1)),
]


@pytest.mark.parametrize(("space", "value"), ALPHA_CARRYING)
def test_alpha_entered_twice(space, value):
    """An alpha keyword agreeing with the value's own alpha is accepted."""
    assert Color(**{space: value}, alpha=1).alpha == 1


@pytest.mark.parametrize(("space", "value"), ALPHA_CARRYING)
def test_alpha_entered_twice_disagreeing(space, value):
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color(**{space: value}, alpha=0.5)


def test_hsla_alpha_is_compared_on_its_own_scale():
    """hsla carries alpha in [0, 100] while the keyword is always [0, 1]."""
    assert Color(hsla=(300, 50, 50, 50), alpha=0.5).alpha == 0.5
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color(hsla=(300, 50, 50, 50), alpha=50)


@pytest.mark.parametrize(
    ("value", "space"),
    [
        ((255, 200, 200, 200), "rgba"),
        ((300, 50, 50, 50), "hsla"),
    ],
)
def test_four_component_sequences_are_identified(value, space):
    """A four-component sequence outside the other format's ranges is not
    ambiguous, so it identifies, and it keeps the alpha it carries."""
    positional = Color(value)
    keyword = Color(**{space: value})
    assert positional == keyword
    assert positional.alpha == keyword.alpha
    assert positional.alpha != 1


def test_four_component_sequence_alpha_can_be_confirmed():
    assert Color((255, 200, 200, 200), alpha=200 / 255.0).alpha == 200 / 255.0
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color((255, 200, 200, 200), alpha=0.1)


@pytest.mark.parametrize("cls", [Color, Colour])
def test_copying_a_color_keeps_its_alpha(cls):
    """Copying a colour is not a way to lose its alpha.

    The conversion to HSL drops it, exactly as it does for a four-component
    sequence, so the constructor has to put it back."""
    original = cls(rgba=(255, 0, 0, 128))
    copy = Color(original)
    assert copy == original
    assert copy.alpha == original.alpha
    assert copy.alpha != 1
    assert copy.rgba == original.rgba


def test_copying_an_opaque_color_stays_opaque():
    assert Color(Color("red")).alpha == 1


def test_copying_a_color_does_not_copy_its_equality_strategy():
    """The constructor copies the colour's value, not how it is compared.

    ``equality`` is a comparison policy rather than part of the colour, and no
    other input format can carry one, so it is not something ``Color(other)``
    inherits. ``copy.copy`` is the way to duplicate both. This is deliberate:
    ``__hash__`` is keyed on ``hex_l`` whatever ``equality`` says, so a copy
    that inherited a custom strategy would spread that inconsistency rather
    than contain it."""
    original = Color("red", equality=HSL_equivalence)
    assert Color(original).equality is RGB_equivalence
    assert copy.copy(original).equality is HSL_equivalence
    assert original.equality is HSL_equivalence


def test_copying_a_color_takes_the_alpha_keyword_over_the_original():
    """Unlike the four-component sequences, a disagreement is not an error.

    A Color always carries an alpha, so there is no way to pass one without
    also stating an alpha to contradict, which would leave no way to restate
    an existing colour's opacity."""
    original = Color(rgba=(255, 0, 0, 128))
    assert Color(original, alpha=0.25).alpha == 0.25
    assert Color(Color("red"), alpha=0.25).alpha == 0.25
    assert original.alpha != 1  # the original is left alone


def test_bad_identify_color():
    with pytest.raises(TypeError, match="Cannot identify color."):
        identify_color("a")
    with pytest.raises(
        TypeError, match="Cannot determine whether color is RGBA or HSLA."
    ):
        identify_color((0, 0, 0, 0))


def test_RGB():
    assert RGB.WHITE == (255.0, 255.0, 255.0)
    assert RGB.BLUE == (0.0, 0.0, 255.0)
    with pytest.raises(AttributeError):
        RGB.DONOTEXISTS  # noqa: B018


def test_HEX():
    assert HEX.WHITE == "#fff"
    assert HEX.BLUE == "#00f"
    with pytest.raises(AttributeError):
        HEX.DONOTEXISTS  # noqa: B018


def test_color_scale_num_sections():
    Color("white")
    n = 10
    cs = color_scale(
        (Color("black"), Color("orange"), Color("blue"), Color("white")), n
    )
    assert cs == [
        Color("black"),
        Color("#39221c"),
        Color("#8e4d1c"),
        Color("orange"),
        Color("#ff003c"),
        Color("#e100ff"),
        Color("blue"),
        Color("#bd71e3"),
        Color("#e3c6d9"),
        Color("white"),
    ]
    assert len(cs) == n

    n = 12
    cs = color_scale(
        (Color("black"), Color("orange"), Color("blue"), Color("white")), n
    )
    assert cs == [
        Color("black"),
        Color("#39221c"),
        Color("#8e4d1c"),
        Color("orange"),
        Color("#ff0004"),
        Color("#ff00ac"),
        Color("#a900ff"),
        Color("blue"),
        Color("#9f58e7"),
        Color("#df9fdf"),
        Color("#e7d7df"),
        Color("white"),
    ]
    assert len(cs) == n

    n = 4
    cs = color_scale(
        (Color(hsl=(0, 100, 50)), Color(hsl=(360, 100, 50))), n, longer=True
    )
    assert cs == [Color("#f00"), Color("#0f0"), Color("#00f"), Color("#f00")]
    assert len(cs) == n

    n = 4
    cs = color_scale(
        (Color(hsl=(360, 100, 50)), Color(hsl=(0, 100, 50))), n, longer=True
    )
    assert len(cs) == n
    assert cs == [Color("#f00"), Color("#00f"), Color("#0f0"), Color("#f00")]

    n = 4
    cs = color_scale((Color(hsl=(0, 100, 50)), Color(hsl=(360, 100, 50))), n)
    assert len(cs) == n
    assert cs == [
        Color("#f00"),
        Color("#f00"),
        Color("#f00"),
        Color("#f00"),
    ]

    n = 4
    cs = color_scale((Color(hsl=(360, 100, 50)), Color(hsl=(0, 100, 50))), n)
    assert len(cs) == n
    assert cs == [
        Color("#f00"),
        Color("#f00"),
        Color("#f00"),
        Color("#f00"),
    ]

    n = 4
    cs = color_scale(
        (Color(hsl=(360.0 / 3, 100, 50)), Color(hsl=(2 * 360.0 / 3, 100, 50))), n
    )
    assert len(cs) == n
    assert cs == [Color("#0f0"), Color("#0fa"), Color("#0af"), Color("#00f")]

    n = 4
    cs = color_scale(
        (Color(hsl=(360.0 / 3, 100, 50)), Color(hsl=(2 * 360.0 / 3, 100, 50))),
        n,
        longer=True,
    )
    assert len(cs) == n
    assert cs == [Color("#0f0"), Color("#fa0"), Color("#f0a"), Color("#00f")]

    n = 4
    cs = color_scale(
        (Color(hsl=(2 * 360.0 / 3, 100, 50)), Color(hsl=(360.0 / 3, 100, 50))),
        n,
        longer=True,
    )
    assert len(cs) == n
    assert cs == [Color("#00f"), Color("#f0a"), Color("#fa0"), Color("#0f0")]

    n = 16
    cs = color_scale((Color(hsl=(0, 0, 0)), Color(hsl=(0, 0, 100))), n)
    assert len(cs) == n
    assert cs == [
        Color("#000"),
        Color("#111"),
        Color("#222"),
        Color("#333"),
        Color("#444"),
        Color("#555"),
        Color("#666"),
        Color("#777"),
        Color("#888"),
        Color("#999"),
        Color("#aaa"),
        Color("#bbb"),
        Color("#ccc"),
        Color("#ddd"),
        Color("#eee"),
        Color("#fff"),
    ]


def test_RGB_color_picker():
    assert RGB_color_picker("Something") == RGB_color_picker("Something")
    assert RGB_color_picker("Something") != RGB_color_picker("Something else")
    assert isinstance(RGB_color_picker("Something"), Color)
    ## The picker takes str(obj), so unlike pick_for it is stable across
    ## processes and can be pinned.
    assert RGB_color_picker("Something").hex_l == "#f58146"


def test_RGB_color_picker_uses_the_whole_cube():
    """It scaled the digest to [0, 1] and then handed it to rgb2hex, which
    reads [0, 255], so every channel rounded to 0 or 1 and only eight colours
    were reachable."""
    colors = [RGB_color_picker(f"user:{i}") for i in range(500)]
    assert len({c.hex_l for c in colors}) == 500
    channels = [ch for c in colors for ch in c.rgb]
    assert max(channels) > 250
    assert min(channels) < 5
    assert 100 < sum(channels) / len(channels) < 155


def test_hash_or_str_falls_back_to_type_qualified_string_for_unhashable_objects():
    class SameStringA:
        def __hash__(self) -> int:
            raise TypeError("unhashable")

        def __str__(self):
            return "shared"

    class SameStringB:
        def __hash__(self) -> int:
            raise TypeError("unhashable")

        def __str__(self):
            return "shared"

    assert hash_or_str(SameStringA()) == "SameStringAshared"
    assert hash_or_str(SameStringB()) == "SameStringBshared"


def test_hsv_constructor():
    assert Color(hsv=(0, 100, 100)) == Color("red")
    assert Color(hsv=(120, 100, 100)) == Color("lime")
    assert Color(hsv=(0, 0, 100)) == Color("white")
    assert Color(hsv=(0, 0, 0)) == Color("black")


def test_colour():
    assert Colour("red") == Color("red")


def test_only_one_input():
    with pytest.raises(ValueError):
        Color(color="red", pick_for="foo")


def test_pick_for():
    """Equal keys give one colour, different keys give different ones.

    The keys are unhashable on purpose. hash_or_str falls back to a string for
    those, whereas a hashable key goes through hash(), which is salted per
    process -- so the colour, and whether a given pair of keys collides, would
    vary from run to run. That was what the xfail on this test covered: with
    RGB_color_picker collapsing every digest onto eight near-black colours,
    two arbitrary keys collided about half the time, and the test only passed
    reliably because object() lands at a predictable address under pytest.
    """
    assert Color(pick_for=[1, 2]) == Color(pick_for=[1, 2])
    assert Color(pick_for=[1, 2]) != Color(pick_for=[3, 4])
    ## pinned, so a regression in the picker cannot pass by being merely
    ## self-consistent
    assert Color(pick_for=[1, 2]).hex_l == "#5162f9"
    assert Color(pick_for=[3, 4]).hex_l == "#3594b1"


def test_pick_for_is_stable_within_a_process():
    """True for any key, hashable or not, since the pick key is computed once."""
    foo = object()
    assert Color(pick_for=foo) == Color(pick_for=foo)


def test_cannot_identify():
    with pytest.raises(TypeError):
        Color((0, 0, 0))
    with pytest.raises(TypeError):
        Color((255, 0, 0))


def test_color_str():
    c = Color("red")
    assert str(c) == "red"
    assert repr(c) == "<Color red>"


def test_purple_inputs():
    assert (
        Color("purple")
        == Color("#800080")
        == Color(hsl=(300, 100, 25.098039215686274))
        == Color(hsla=(300, 100, 25.098039215686274, 100.0))
        == Color(hslf=(300 / 360, 1, 0.25098039215686274))
        == Color(hslaf=(300 / 360, 1, 0.25098039215686274, 1.0))
        == Color((300, 100, 25.098039215686274))
        == Color(Color("purple"))
    )


def test_red_inputs():
    assert (
        Color("red")
        == Color("blue", hue=0)
        == Color("#f00")
        == Color("#ff0000")
        == Color(hsl=(0, 100, 50))
        == Color(hsla=(0, 100, 50, 100))
        == Color(rgb=(255, 0, 0))
        == Color(rgba=(255, 0, 0, 255))
        == Color(rgbf=(1, 0, 0))
        == Color(rgbaf=(1, 0, 0, 1))
        == Color(Color("red"))
    )


def test_blue_inputs():
    assert (
        Color("blue")
        == Color("#00f")
        == Color("#0000ff")
        == Color(hsl=(240, 100, 50))
        == Color(hsla=(240, 100, 50, 100))
        == Color(rgb=(0, 0, 255))
        == Color(rgba=(0, 0, 255, 255))
        == Color(rgbf=(0, 0, 1))
        == Color(rgbaf=(0, 0, 1, 1))
        == Color((0, 0, 255))
        == Color(Color("blue"))
    )


def test_comparison_with_non_color_is_false():
    """Comparing against a non-color returns NotImplemented, and so is False."""
    assert Color("red") != "red"
    ## `==` is exercised directly: it is the operator that used to raise.
    assert not (Color("red") == "red")  # noqa: SIM201
    assert Color("red") != 42
    assert Color("red") != None  # noqa: E711
    assert Color("red") != "red"


def test_comparison_with_non_color_does_not_raise_in_containers():
    """The old NotImplementedError broke any mixed collection."""
    assert Color("red") in [1, "red", Color("red")]
    assert Color("blue") not in [1, "red", Color("red")]
    assert [Color("red"), "red"].count("red") == 1


def test_no_attribute():
    """Unknown attributes are now visible to the type checker too."""
    c = Color("red")
    with pytest.raises(AttributeError):
        c.does_not_exists  # type: ignore  # noqa: B018
    with pytest.raises(AttributeError):
        c.get_does_not_exists  # type: ignore  # noqa: B018


def test_cannot_set_unknown_attribute():
    """__slots__ keeps a mistyped attribute an error rather than a silent set."""
    c = Color("red")
    with pytest.raises(AttributeError):
        c.does_not_exists = 1  # type: ignore
    with pytest.raises(AttributeError):
        Color("red", does_not_exists=1)
    with pytest.raises(AttributeError):
        Colour("red", does_not_exists=1)


def test_read_only_attributes_cannot_be_assigned():
    c = Color("red")
    for attribute in ("hsla", "hslf", "hslaf", "luminance"):
        with pytest.raises(AttributeError):
            setattr(c, attribute, 0)


def test_accessors_remain_available():
    """The get_*/set_* methods stay part of the API."""
    c = Color("red")
    assert c.get_hex_l() == "#ff0000"
    assert c.get_rgb() == c.rgb
    c.set_hue(240)
    assert c.web == "blue"


def test_attributes_are_discoverable():
    """Properties are visible on the class, unlike the old dynamic dispatch."""
    for attribute in ("hsl", "rgb", "rgba", "hsla", "hex", "web", "luminance"):
        assert isinstance(getattr(Color, attribute), property)
        assert attribute in dir(Color("red"))


def test_web1():
    red = Color("red")
    blue = Color("blue")
    red.web = "blue"
    assert red == blue


def test_rgb():
    blue1 = Color(rgb=(0, 0, 255))
    blue = Color("blue")
    assert blue1 == blue


def test_hex_l():
    blue1 = Color(hex_l="#0000ff")
    blue = Color("blue")
    assert blue1 == blue


def test_hex():
    blue1 = Color(hex="#00f")
    blue = Color("blue")
    assert blue1 == blue


def test_web():
    blue1 = Color(web="blue")
    blue = Color("blue")
    assert blue1 == blue


def test_get_luminance():
    blue = Color("blue")
    assert round(blue.luminance, 4) == 0.3376


def test_color_range_to():
    red = Color("red")
    blue = Color("blue")
    assert list(red.range_to(blue, 5)) == [
        Color("red"),
        Color("#ff007f"),
        Color("magenta"),
        Color("#7f00ff"),
        Color("blue"),
    ]
    black = Color("black")
    white = Color("white")
    assert list(black.range_to(white, 6)) == [
        Color("black"),
        Color("#333"),
        Color("#666"),
        Color("#999"),
        Color("#ccc"),
        Color("white"),
    ]
    lime = Color("lime")
    assert list(red.range_to(lime, 5)) == [
        Color("red"),
        Color("#ff7f00"),
        Color("yellow"),
        Color("chartreuse"),
        Color("lime"),
    ]


def test_HSL_equivalence():
    black_red = Color("red", hue=0, equality=HSL_equivalence)
    black_blue = Color("blue", hue=0, equality=HSL_equivalence)
    assert black_red == black_blue


def test_color_access():
    b = Color("black")
    b.hsl = HSL.BLUE
    assert round(b.hue / 360.0, 4) == 0.6667
    assert b.saturation == 100.0
    assert b.lightness == 50
    assert b.red == 0.0
    assert b.blue == 255.0
    assert b.green == 0.0
    assert b.rgb == (0.0, 0.0, 255.0)
    assert b.rgbf == (0.0, 0.0, 1.0)
    assert b.rgba == (0.0, 0.0, 255.0, 255.0)
    assert b.rgbaf == (0.0, 0.0, 1.0, 1.0)
    assert round(b.hsl[0] / 360.0, 4) == 0.6667
    assert b.hsl[1:] == (100.0, 50)
    assert b.hex == "#00f"


def test_thresholding():
    c = Color("lime")
    assert c.rgb[0] == 0
    assert c.rgb[2] == 0


def test_color_setters():
    b = Color("black")
    b.hsl = HSL.BLUE
    assert b.hsl == (240.0, 100.0, 50.0)
    b.rgb = (0.0, 0.0, 255.0)
    assert b.rgb == (0.0, 0.0, 255.0)
    b.hex = "#f00"
    assert b.hex == "#f00"
    b.hex = "#ff0000"
    assert b.hex_l == "#ff0000"
    assert b.hex == "#f00"
    b.hsl = (0.0, 100.0, 50.0)
    assert b.hsl == (0.0, 100.0, 50.0)
    b.rgba = (0.0, 0.0, 255.0, 255.0)
    assert b.rgba == (0.0, 0.0, 255.0, 255.0)
    b.rgbaf = (0.0, 0.0, 1.0, 1.0)
    assert b.rgbaf == (0.0, 0.0, 1.0, 1.0)
    b.rgb = (0.0, 0.0, 255.0)
    assert b.rgb == (0.0, 0.0, 255.0)
    b.rgbf = (0.0, 0.0, 1.0)
    assert b.rgbf == (0.0, 0.0, 1.0)


def test_color_change_values():
    b = Color("black")
    b.hsl = HSL.BLUE
    b.hue = 0.0
    assert b.hex == "#f00"
    b.hue = 2.0 / 3 * 360.0
    assert b.hex == "#00f"
    b.hex = "#f00"
    assert b.hsl == (0.0, 100.0, 50.0)

    b.hex_l = "#123456"
    assert b.hex_l == "#123456"
    assert b.hex == "#123456"

    b.hex_l = "#ff0000"
    assert b.hex_l == "#ff0000"
    assert b.hex == "#f00"


def test_color_properties():
    c = Color("blue")
    c.hue = 0
    assert c == Color("red")

    c.saturation = 0.0
    assert c.hsl == (0, 0.0, 50.0)
    assert c.rgb == (0.5 * 255.0, 0.5 * 255.0, 0.5 * 255.0)

    c.lightness = 0.0
    assert Color("black") == c
    assert c.hex == "#000"

    c.green = 1.0 * 255.0
    c.blue = 1.0 * 255.0
    assert c.hex == "#0ff"
    assert c == Color("cyan")

    c = Color("blue", lightness=75)
    assert c.web == "#7f7fff"

    c = Color("red", red=0.5 * 255.0)
    assert c.web == "#7f0000"


def test_color_recursive_init():
    assert Color("red") == Color(Color(Color("red")))


def test_alpha():
    c = Color("red")
    assert c.alpha == 1
    assert c.rgb == (255.0, 0.0, 0.0)
    assert c.rgba == (255.0, 0.0, 0.0, 255.0)
    assert c.rgbf == (1.0, 0.0, 0.0)
    assert c.rgbaf == (1.0, 0.0, 0.0, 1.0)
    assert c.hsl == (0, 100.0, 50.0)
    assert c.hsla == (0, 100.0, 50.0, 100.0)
    assert c.hslf == (0, 1.0, 0.5)
    assert c.hslaf == (0, 1.0, 0.5, 1.0)
    c.alpha = 0.5
    assert c.alpha == 0.5
    assert c.rgb == (255.0, 0.0, 0.0)
    assert c.rgba == (255.0, 0.0, 0.0, 127.5)
    assert c.rgbf == (1.0, 0.0, 0.0)
    assert c.rgbaf == (1.0, 0.0, 0.0, 0.5)
    assert c.hsl == (0, 100.0, 50.0)
    assert c.hsla == (0, 100, 50, 50)
    assert c.hslf == (0, 1.0, 0.5)
    assert c.hslaf == (0, 1, 0.5, 0.5)
    with pytest.raises(ValueError):
        c.alpha = -0.1
    with pytest.raises(ValueError):
        c.alpha = 1.1


def test_color_equality():
    assert Color("red") != Color("blue")
    assert Color("red") == Color("red")
    assert Color("red") != Color("blue")
    assert Color("red") == Color("red")


def test_color_equality_change():
    def saturation_equality(c1, c2):
        return c1.lightness == c2.lightness

    assert Color("red", equality=saturation_equality) == Color("blue")


def test_color_subclassing():
    class Tint(Color):
        pass

    assert Tint("red").hsl == (0.0, 100.0, 50)


def test_keyword_arguments_set_writable_properties():
    assert Color("red", lightness=0).hsl == (0.0, 100.0, 0.0)
    assert Color("red", lightness=0, saturation=25).hsl == (0.0, 25.0, 0.0)


def test_keyword_arguments_are_validated_by_the_property_they_set():
    with pytest.raises(InvalidColorError, match="Value is not a valid HSL"):
        Color("red", lightness=200)


def test_keyword_arguments_are_not_arbitrary_attributes():
    """``__slots__`` is what makes a mistyped name an error rather than a
    silent new attribute, and that applies to the constructor too."""
    with pytest.raises(AttributeError, match="no attribute 'foo'"):
        Color("red", foo=1)
    with pytest.raises(AttributeError, match="has no setter"):
        Color("red", luminance=0.5)


def test_keyword_arguments_do_not_reach_the_stored_attributes():
    """Assigning a slot directly would skip the property that validates it.

    ``_hsl`` accepts any three objects and ``_alpha`` any number, so without
    this the constructor could build a colour that only fails later, at some
    unrelated call."""
    with pytest.raises(ValueError, match="is stored state"):
        Color("red", _hsl=("not", "a", "colour"))
    with pytest.raises(ValueError, match="is stored state"):
        Color("red", _alpha=99)


def test_a_subclass_without_slots_does_take_arbitrary_attributes():
    """The one place the old docstring was right, kept working on purpose."""

    class Tint(Color):
        pass

    assert Tint("red", foo=1).foo == 1  # type: ignore
    ## The guard is on the name, not on where it would have been stored, so a
    ## subclass cannot reach the slots either.
    with pytest.raises(ValueError, match="is stored state"):
        Tint("red", _hsl=(1, 2, 3))


def test_color_factory():
    get_color = make_color_factory(
        equality=HSL_equivalence, picker=RGB_color_picker, pick_key=str
    )
    black_red = get_color("red", lightness=0)
    black_blue = get_color("blue", lightness=0)
    assert isinstance(black_red, Color)
    assert black_red != black_blue


def test_color_color_lower():
    assert Color("orangered") == Color("OrangeRed")


def test_color_web_lower():
    assert Color(web="orangered") == Color(web="OrangeRed")


TUPLE_ATTRIBUTES = ("hsl", "hsla", "hslf", "hslaf", "rgb", "rgba", "rgbf", "rgbaf")
SCALAR_ATTRIBUTES = (
    "hue",
    "saturation",
    "lightness",
    "red",
    "green",
    "blue",
    "alpha",
    "luminance",
)


def assert_all_float(color):
    for attribute in TUPLE_ATTRIBUTES:
        for component in getattr(color, attribute):
            assert type(component) is float, f"{attribute} component is not a float"
    for attribute in SCALAR_ATTRIBUTES:
        assert type(getattr(color, attribute)) is float, f"{attribute} is not a float"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"color": "red"},
        {"web": "blue"},
        {"hex": "#00f"},
        {"hsl": (240, 100, 50)},
        {"hsla": (240, 100, 50, 100)},
        {"hslf": (0, 1, 1)},
        {"hslaf": (0, 1, 1, 1)},
        {"rgb": (0, 0, 255)},
        {"rgba": (0, 0, 255, 255)},
        {"rgbf": (0, 0, 1)},
        {"rgbaf": (0, 0, 1, 1)},
        {"color": "red", "alpha": 1},
    ],
)
def test_attributes_are_float_for_integer_input(kwargs):
    """Integer input must not leak into the attributes as ints."""
    assert_all_float(Color(**kwargs))


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("hue", 0),
        ("saturation", 50),
        ("lightness", 25),
        ("red", 12),
        ("green", 7),
        ("blue", 3),
        ("alpha", 1),
        ("hsl", (240, 100, 50)),
        ("rgb", (0, 0, 255)),
    ],
)
def test_attributes_are_float_after_integer_assignment(attribute, value):
    c = Color("red")
    setattr(c, attribute, value)
    assert_all_float(c)


def test_setting_one_hsl_channel_does_not_mix_types():
    """Assigning one channel used to leave the tuple as (int, float, float)."""
    c = Color("red")
    c.hue = 240
    assert c.hsl == (240.0, 100.0, 50.0)
    assert [type(v) for v in c.hsl] == [float, float, float]


def test_bool_input_is_normalized_to_float():
    """bool is an int subclass and must not survive into the attributes."""
    assert_all_float(Color(hslf=(0, True, True)))


def test_color_errors_are_catchable_as_one_kind():
    """Every bad-colour failure derives from ColorError."""
    cases = [
        lambda: Color("nope"),
        lambda: Color((0, 0, 0)),
        lambda: Color(hslf=(2, 0, 0)),
        lambda: setattr(Color("red"), "hsl", (0, 102, 0)),
        lambda: setattr(Color("red"), "alpha", 2),
    ]
    for case in cases:
        with pytest.raises(ColorError):
            case()


def test_same_failure_raises_the_same_error():
    """An invalid HSL used to be ValueError here and TypeError there."""
    with pytest.raises(InvalidColorError):
        hsl2rgb((0, 102, 0))
    with pytest.raises(InvalidColorError):
        Color("red").set_hsl((0, 102, 0))


def test_error_kinds_are_distinguishable():
    with pytest.raises(AmbiguousColorError):
        Color((0, 0, 0))
    with pytest.raises(UnknownColorError):
        Color("nope")
    with pytest.raises(InvalidColorError):
        Color(hslf=(2, 0, 0))


def test_errors_stay_catchable_as_before():
    """ColorError derives from both ValueError and TypeError for compatibility."""
    assert issubclass(ColorError, ValueError)
    assert issubclass(ColorError, TypeError)
    for error in (InvalidColorError, AmbiguousColorError, UnknownColorError):
        assert issubclass(error, ColorError)
    with pytest.raises(ValueError):
        hsl2rgb((0, 102, 0))
    with pytest.raises(TypeError):
        Color((0, 0, 0))
    with pytest.raises(TypeError):
        Color("red").set_hsl((0, 102, 0))
    with pytest.raises(ValueError):
        Color("nope")


def test_usage_errors_are_not_color_errors():
    """Calling a helper wrongly is not a bad colour, and stays a plain error."""
    with pytest.raises(ValueError) as excinfo:
        color_scale((Color("red"),), 5)
    assert not isinstance(excinfo.value, ColorError)
    with pytest.raises(TypeError) as excinfo:
        Color("red").preview(size_x="wide")  # type: ignore
    assert not isinstance(excinfo.value, ColorError)


def test_color_is_hashable():
    assert hash(Color("red")) == hash(Color("#f00"))
    assert len({Color("red"), Color("#ff0000"), Color("blue")}) == 2
    assert {Color("red"): "warm"}[Color("#f00")] == "warm"


def test_hash_matches_equality():
    """Equal colors must hash equally, for both built-in strategies."""
    for a, b in [
        (Color("red"), Color("#f00")),
        (Color("red", alpha=0.5), Color("red")),
        (Color("red", equality=HSL_equivalence), Color("#ff0000")),
    ]:
        assert a == b
        assert hash(a) == hash(b)


def test_hash_follows_mutation():
    c = Color("red")
    before = hash(c)
    c.hue = 240
    assert hash(c) == hash(Color("blue"))
    assert hash(c) != before


def test_equality_is_symmetric_across_strategies():
    """a == b and b == a used to disagree when strategies differed."""
    a = Color("red", lightness=0, equality=HSL_equivalence)
    b = Color("blue", lightness=0)
    assert (a == b) == (b == a)

    def never_equal(c1, c2):
        return False

    c = Color("red", equality=never_equal)
    d = Color("red")
    assert (c == d) == (d == c)


def test_equality_unchanged_when_strategies_agree():
    assert Color("red") == Color("#f00")
    assert Color("red") != Color("blue")
    black_red = Color("red", hue=0, equality=HSL_equivalence)
    black_blue = Color("blue", hue=0, equality=HSL_equivalence)
    assert black_red == black_blue
    red = Color("red", lightness=0, equality=HSL_equivalence)
    blue = Color("blue", lightness=0, equality=HSL_equivalence)
    assert red != blue


def test_colour_alias_compares_and_hashes_with_color():
    assert Colour("red") == Color("red")
    assert Color("red") == Colour("red")
    assert hash(Colour("red")) == hash(Color("red"))
    assert len({Color("red"), Colour("red")}) == 1


def test_hsv_attribute():
    assert Color("red").hsv == pytest.approx((0.0, 100.0, 100.0))
    assert Color("white").hsv == pytest.approx((0.0, 0.0, 100.0))
    assert Color("black").hsv == pytest.approx((0.0, 0.0, 0.0))
    assert Color("blue").hsv.value == 100.0
    assert Color("red").hsv.hue == 0.0
    assert Color("red").hsv.saturation == 100.0


def test_hsv_is_settable():
    c = Color("red")
    c.hsv = (240, 100, 100)
    assert c.web == "blue"
    c.hsv = (0, 0, 100)
    assert c.web == "white"


def test_hsv_round_trips_through_color():
    for name in ("red", "rebeccapurple", "white", "black", "olive", "teal"):
        original = Color(name)
        assert Color(hsv=original.hsv).hex_l == original.hex_l


def test_hsv_components_are_floats():
    assert [type(v) for v in Color(hsv=(120, 50, 50)).hsv] == [float, float, float]


def test_hsv_must_be_named():
    """An HSV triple is indistinguishable from an HSL one, so it is not guessed."""
    with pytest.raises(AmbiguousColorError):
        Color((0, 100, 100))
    assert Color(hsv=(0, 100, 100)) == Color("red")
    assert Color(hsl=(0, 100, 100)) == Color("white")


def test_hsv_conflicts_with_other_inputs():
    with pytest.raises(ValueError, match="Only one of"):
        Color(hsv=(0, 100, 100), rgb=(255, 0, 0))
    with pytest.raises(ValueError, match="'hsv'"):
        Color()


def test_bad_hsv_via_color():
    with pytest.raises(InvalidColorError):
        Color(hsv=(361, 0, 0))
    with pytest.raises(InvalidColorError):
        Color("red").set_hsv((0, 101, 0))


SPACES = ("xyz", "lab", "lch", "oklab", "oklch", "cmyk", "yuv", "hsv")


@pytest.mark.parametrize("space", SPACES)
def test_space_round_trips_through_color(space):
    for name in ("red", "rebeccapurple", "white", "black", "olive", "teal", "gold"):
        original = Color(name)
        assert Color(**{space: getattr(original, space)}).hex_l == original.hex_l


@pytest.mark.parametrize("space", SPACES)
def test_space_components_are_floats(space):
    assert all(type(v) is float for v in getattr(Color("rebeccapurple"), space))


def test_space_reference_values_via_color():
    red = Color("red")
    assert red.xyz == pytest.approx((41.2456, 21.2673, 1.9334), abs=1e-3)
    assert red.lab == pytest.approx((53.2408, 80.0925, 67.2032), abs=1e-3)
    assert red.lch == pytest.approx((53.2408, 104.5518, 39.999), abs=1e-3)
    assert red.oklab == pytest.approx((0.62796, 0.22486, 0.12585), abs=1e-5)
    assert red.oklch == pytest.approx((0.62796, 0.25768, 29.2339), abs=1e-4)
    assert red.cmyk == (0.0, 100.0, 100.0, 0.0)
    assert red.yuv == pytest.approx((0.299, -0.147108, 0.614777), abs=1e-6)


def test_spaces_are_settable():
    c = Color("red")
    c.lab = Color("blue").lab
    assert c.web == "blue"
    c.cmyk = (100, 0, 0, 0)
    assert c.hex_l == "#00ffff"
    c.yuv = Color("lime").yuv
    assert c.web == "lime"
    c.oklab = Color("red").oklab
    assert c.web == "red"
    c.oklch = Color("blue").oklch
    assert c.web == "blue"


def test_space_named_fields():
    red = Color("red")
    assert red.lab.lightness == pytest.approx(53.2408, abs=1e-3)
    assert red.lch.chroma == pytest.approx(104.5518, abs=1e-3)
    assert red.oklab.lightness == pytest.approx(0.62796, abs=1e-5)
    assert red.oklch.chroma == pytest.approx(0.25768, abs=1e-5)
    assert red.cmyk.key == 0.0
    assert red.yuv.luma == pytest.approx(0.299)
    assert red.xyz.y == pytest.approx(21.2673, abs=1e-3)


def test_spaces_conflict_with_other_inputs():
    with pytest.raises(ValueError, match="Only one of"):
        Color(lab=(50, 0, 0), rgb=(255, 0, 0))
    with pytest.raises(ValueError, match="'lab'"):
        Color()


@pytest.mark.parametrize(
    ("space", "bad"),
    [
        ("xyz", (-1, 0, 0)),
        ("lab", (101, 0, 0)),
        ("lch", (0, 0, 361)),
        ("oklab", (1.1, 0, 0)),
        ("oklch", (0, 0.41, 0)),
        ("cmyk", (101, 0, 0, 0)),
        ("yuv", (1.1, 0, 0)),
    ],
)
def test_bad_space_input_via_color(space, bad):
    with pytest.raises(InvalidColorError):
        Color(**{space: bad})
    with pytest.raises(InvalidColorError):
        setattr(Color("red"), space, bad)


SCALE_SPACES = ("hsl", "lab", "lch", "oklab", "oklch")


def test_color_scale_default_space_is_unchanged():
    """HSL stays the default, so this output is a backward-compatibility guard."""
    assert [c.hex_l for c in color_scale((Color("blue"), Color("yellow")), 5)] == [
        "#0000ff",
        "#bf00ff",
        "#ff007f",
        "#ff4000",
        "#ffff00",
    ]
    assert color_scale((Color("blue"), Color("yellow")), 5) == color_scale(
        (Color("blue"), Color("yellow")), 5, space="hsl"
    )


@pytest.mark.parametrize("space", SCALE_SPACES)
def test_color_scale_keeps_endpoints_in_every_space(space):
    stops = (Color("blue"), Color("black"), Color("orange"), Color("white"))
    scale = color_scale(stops, 10, space=space)
    assert len(scale) == 10
    assert scale[0] == stops[0]
    assert scale[-1] == stops[-1]
    ## every control colour survives as one of the steps
    for stop in stops:
        assert stop in scale


@pytest.mark.parametrize("space", SCALE_SPACES)
def test_color_scale_exact_inputs_in_every_space(space):
    stops = (Color("blue"), Color("black"), Color("blue"), Color("orange"))
    assert color_scale(stops, 4, space=space) == list(stops)


def test_color_scale_rejects_unknown_space():
    with pytest.raises(ValueError, match="Unknown interpolation space 'srgb'"):
        color_scale((Color("red"), Color("blue")), 5, space="srgb")


@pytest.mark.parametrize("space", ("lab", "oklab"))
def test_color_scale_rejects_longer_without_a_hue(space):
    with pytest.raises(ValueError, match="no hue channel"):
        color_scale((Color("red"), Color("blue")), 5, longer=True, space=space)


def test_color_scale_longer_takes_the_other_arc_in_oklch():
    short = color_scale((Color("red"), Color("blue")), 5, space="oklch")
    long = color_scale((Color("red"), Color("blue")), 5, longer=True, space="oklch")
    assert short != long
    assert short[0] == long[0] == Color("red")
    assert short[-1] == long[-1] == Color("blue")

    ## Red is at hue 29 and blue at 264. The short arc runs backwards through
    ## magenta; only the long one crosses the greens between them.
    greens = range(100, 200)
    assert not any(int(c.oklch.hue) in greens for c in short)
    assert any(int(c.oklch.hue) in greens for c in long)


def _oklab_distance(c1, c2):
    return math.dist(c1.oklab, c2.oklab)


def _step_evenness(scale):
    """Ratio of the largest to the smallest perceived step. 1.0 is perfect."""
    steps = [_oklab_distance(a, b) for a, b in zip(scale[:-1], scale[1:], strict=True)]
    return max(steps) / min(steps)


SCALE_PAIRS = [
    ("blue", "yellow"),
    ("red", "cyan"),
    ("magenta", "green"),
    ("red", "blue"),
    ("black", "white"),
]


@pytest.mark.parametrize(("start", "end"), SCALE_PAIRS)
def test_oklab_steps_are_more_even_than_hsl(start, end):
    """The point of the exercise: Oklab is within 5% of a perfect ramp."""
    stops = (Color(start), Color(end))
    assert _step_evenness(color_scale(stops, 9, space="oklab")) < 1.05
    assert _step_evenness(color_scale(stops, 9, space="hsl")) > 2.5


def test_hsl_brightness_is_not_monotonic_where_oklab_is():
    """An HSL ramp between complementary colours rises, dips, then rises."""
    stops = (Color("blue"), Color("yellow"))
    hsl = [c.oklab.lightness for c in color_scale(stops, 9)]
    oklab = [c.oklab.lightness for c in color_scale(stops, 9, space="oklab")]

    assert not all(a <= b for a, b in zip(hsl[:-1], hsl[1:], strict=True))
    assert hsl[3] > hsl[4]  # the dip
    assert all(a < b for a, b in zip(oklab[:-1], oklab[1:], strict=True))


@pytest.mark.parametrize(("start", "end"), [("red", "cyan"), ("black", "white")])
def test_oklab_steps_are_exactly_equal_inside_the_gamut(start, end):
    scale = color_scale((Color(start), Color(end)), 9, space="oklab")
    lightness = [c.oklab.lightness for c in scale]
    deltas = [b - a for a, b in zip(lightness[:-1], lightness[1:], strict=True)]
    assert max(deltas) == pytest.approx(min(deltas), abs=1e-12)


def test_oklab_interpolation_clamps_where_it_leaves_the_gamut():
    """A straight line in Oklab can pass outside sRGB, which has no encoding.

    Blue to yellow does, one step in: the eighth point wants a red channel of
    -0.006, so it is clamped and reads back a shade lighter than asked for.
    """
    scale = color_scale((Color("blue"), Color("yellow")), 9, space="oklab")
    assert scale[1].rgb.red == 0.0
    wanted = [
        a + (b - a) * (1 / 8)
        for a, b in zip(Color("blue").oklab, Color("yellow").oklab, strict=True)
    ]
    assert scale[1].oklab.lightness > wanted[0]
    assert scale[1].oklab == pytest.approx(wanted, abs=5e-3)


def test_hsl_passes_through_hues_in_neither_endpoint():
    """Being polar, HSL swings blue to yellow through magenta and red."""
    scale = color_scale((Color("blue"), Color("yellow")), 9)
    assert any(c.hex_l == "#ff007f" for c in scale)  # a pink, from nowhere
    oklab = color_scale((Color("blue"), Color("yellow")), 9, space="oklab")
    assert all(c.oklab.lightness > 0 for c in oklab)
    ## Oklab stays between the endpoints on both chroma axes
    lo, hi = sorted((Color("blue").oklab.b, Color("yellow").oklab.b))
    assert all(lo - 1e-12 <= c.oklab.b <= hi + 1e-12 for c in oklab)


def test_range_to_accepts_a_space():
    direct = color_scale((Color("red"), Color("blue")), 5, space="oklab")
    assert list(Color("red").range_to("blue", 5, space="oklab")) == direct
    assert list(Color("red").range_to("blue", 5)) != direct


def test_relative_luminance_is_not_luminance():
    """The two are different quantities, and the docstrings now say so.

    Pinned because the names are one word apart and the values are not: using
    `luminance` for contrast is the mistake this pair exists to prevent."""
    grey = Color("#777777")
    assert grey.luminance == pytest.approx(0.4667, abs=0.0001)
    assert grey.relative_luminance == pytest.approx(0.1845, abs=0.0001)
    assert Color("white").relative_luminance == 1.0
    assert Color("black").relative_luminance == 0.0


def test_contrast_ratio_accepts_any_input_format():
    black = Color("black")
    for white in ("white", "#ffffff", "#fff", (255, 255, 255), Color("white")):
        assert black.contrast_ratio(white) == 21.0


def test_contrast_ratio_is_symmetric_and_ignores_alpha():
    """Alpha is deliberately not consulted: a translucent colour has no
    contrast of its own, only the composite does."""
    black, white = Color("black"), Color("white")
    assert black.contrast_ratio(white) == white.contrast_ratio(black) == 21.0
    assert black.contrast_ratio(Color("white", alpha=0.1)) == 21.0
    assert Color("black", alpha=0.1).contrast_ratio(white) == 21.0


## The greys accessibility tooling quotes for each WCAG threshold against
## white, each paired with the next grey up, which is the first to fail it.
## Sitting the tests on the boundary is the point: a threshold that is off by
## one level, or compared with > instead of >=, moves exactly one of these.
@pytest.mark.parametrize(
    ("hex_value", "level", "size", "expected"),
    [
        ("#595959", "AAA", "normal", True),  # 7.0047, the last to clear 7
        ("#5a5a5a", "AAA", "normal", False),  # 6.8969
        ("#767676", "AA", "normal", True),  # 4.5422, the last to clear 4.5
        ("#777777", "AA", "normal", False),  # 4.4781
        ("#767676", "AAA", "large", True),  # AAA large is also 4.5
        ("#777777", "AAA", "large", False),
        ("#949494", "AA", "large", True),  # 3.0335, the last to clear 3
        ("#959595", "AA", "large", False),  # 2.9953
    ],
)
def test_is_readable_sits_on_the_wcag_thresholds(hex_value, level, size, expected):
    assert Color(hex_value).is_readable("white", level=level, size=size) is expected


def test_is_readable_is_symmetric_and_ignores_alpha():
    text, background = Color("#767676"), Color("white")
    assert text.is_readable(background) == background.is_readable(text) is True
    assert text.is_readable(Color("white", alpha=0.1)) is True


def test_is_readable_accepts_either_case():
    assert Color("#767676").is_readable("white", level="aa", size="NORMAL") is True


@pytest.mark.parametrize(
    ("level", "size"),
    [("A", "normal"), ("AA", "huge"), ("AAAA", "large"), ("", "")],
)
def test_is_readable_rejects_a_pair_wcag_does_not_define(level, size):
    with pytest.raises(ValueError, match="No WCAG minimum"):
        Color("white").is_readable("black", level=level, size=size)


def test_best_text_color_defaults_to_black_or_white():
    assert Color("black").best_text_color() == Color("white")
    assert Color("white").best_text_color() == Color("black")
    assert Color("navy").best_text_color() == Color("white")
    assert Color("yellow").best_text_color() == Color("black")


def test_best_text_color_switches_where_the_contrast_does():
    """#757575 is the last grey that white wins on, #767676 the first black does.

    Which is not the midpoint of the range, because relative luminance is not
    linear in the channel value -- picking by lightness instead would put the
    switch in the wrong place."""
    assert Color("#757575").best_text_color() == Color("white")
    assert Color("#767676").best_text_color() == Color("black")


def test_best_text_color_takes_the_candidates_it_is_given():
    assert Color("navy").best_text_color(["#eeeeee", "#333333", "red"]) == Color("#eee")
    assert Color("navy").best_text_color([Color("red")]) == Color("red")


def test_best_text_color_rejects_a_bare_string():
    """A str is a Sequence, so "white" would iterate as five one-letter colours.

    No `type: ignore` here, and that is the point: `str` genuinely satisfies
    `Sequence[str | ...]`, so the annotation cannot rule this out and the check
    has to happen at runtime."""
    with pytest.raises(ValueError, match="not the single color"):
        Color("navy").best_text_color("white")


def test_best_text_color_rejects_an_empty_choice():
    with pytest.raises(ValueError, match="at least one color"):
        Color("navy").best_text_color([])
