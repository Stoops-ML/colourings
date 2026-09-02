import copy
import inspect
import math
import subprocess
import sys
from itertools import pairwise
from unittest.mock import MagicMock, patch

import pytest

from colourings.colour import (
    _ALL_BLEND_MODES,
    _BLEND_MODES,
    _KEYWORD_ALPHA_SCALES,
    _KEYWORD_INPUTS,
    _NONSEPARABLE_BLEND_MODES,
    NAMED_HEX,
    NAMED_HSL,
    NAMED_RGB,
    Color,
    Colour,
    HSL_equivalence,
    RGB_color_picker,
    RGB_equivalence,
    _blend_luma,
    _blend_saturation,
    _set_blend_saturation,
    color_scale,
    colour_scale,
    hash_or_str,
    identify_color,
    make_color_factory,
    stable_key,
)
from colourings.conversions import hsl2rgb, rgb2relative_luminance
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
    mock_root.title.assert_called_once_with(f"{c!s} preview")
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
    with pytest.raises(ValueError, match="At least two colours are required"):
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
        match="Number of steps must be greater than or equal to the number of colors",
    ):
        colour_scale((Color("white"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors",
    ):
        colour_scale((Color("blue"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors",
    ):
        colour_scale((Color("blue"), Color("black"), Color("blue")), 2)


def test_color_scale_with_fewer_inputs():
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors",
    ):
        color_scale((Color("white"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors",
    ):
        color_scale((Color("blue"), Color("black")), 1)
    with pytest.raises(
        ValueError,
        match="Number of steps must be greater than or equal to the number of colors",
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
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
        c.alpha = 2
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
        c.alpha = -0.5


def test_bad_color_change_rgb():
    c = Color("red")
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        c.red = 300
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        c.red = -0.5
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        c.green = 300
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        c.green = -0.5
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        c.blue = 300
    with pytest.raises(ValueError, match="Input is not an RGB type"):
        c.blue = -0.5


def test_bad_color_scale():
    with pytest.raises(ValueError, match="At least two colours are required"):
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
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
        Color(rgb=(1, 1, 1), alpha=-1)
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
        Color(rgb=(1, 1, 1), alpha=1.1)
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color(rgba=(1, 1, 1, 1), alpha=0)
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color(rgba=(1, 1, 1, 1), alpha=1)
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color(rgbaf=(1, 1, 1, 1), alpha=0)
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color(hsla=(1, 1, 1, 1), alpha=0)
    with pytest.raises(ValueError, match="Alpha value defined twice"):
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
    with pytest.raises(TypeError, match="Cannot identify color"):
        identify_color("a")
    with pytest.raises(
        TypeError, match="Cannot determine whether color is RGBA or HSLA"
    ):
        identify_color((0, 0, 0, 0))


@pytest.mark.parametrize(
    "value",
    [
        123,  # neither a string nor a sequence
        None,
        (1, 2),  # a sequence, but of no recognised length
        (1, 2, 3, 4, 5),
        (),
        "nope",  # a string matching no string format
        "rgb(1 2 3",  # not quite a colour function
    ],
)
def test_identify_color_refuses_what_it_cannot_place(value):
    with pytest.raises(UnknownColorError, match="Cannot identify color"):
        identify_color(value)


def test_RGB():
    assert NAMED_RGB.WHITE == (255.0, 255.0, 255.0)
    assert NAMED_RGB.BLUE == (0.0, 0.0, 255.0)
    with pytest.raises(AttributeError):
        NAMED_RGB.DONOTEXISTS  # noqa: B018


def test_HEX():
    assert NAMED_HEX.WHITE == "#fff"
    assert NAMED_HEX.BLUE == "#00f"
    with pytest.raises(AttributeError):
        NAMED_HEX.DONOTEXISTS  # noqa: B018


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
    with pytest.raises(ValueError, match="Only one of 'color'"):
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


def test_pick_for_is_stable_within_a_process_even_for_a_bare_object():
    """An object with the default __repr__ carries its address in its string
    form, so it is the one case the default key cannot make stable across
    processes. Within one, it still holds."""
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
    b.hsl = NAMED_HSL.BLUE
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
    b.hsl = NAMED_HSL.BLUE
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
    b.hsl = NAMED_HSL.BLUE
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
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
        c.alpha = -0.1
    with pytest.raises(ValueError, match="Alpha must be between 0 and 1"):
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
    with pytest.raises(ValueError, match="Input is not an HSL type"):
        hsl2rgb((0, 102, 0))
    with pytest.raises(TypeError):
        Color((0, 0, 0))
    with pytest.raises(TypeError):
        Color("red").set_hsl((0, 102, 0))
    with pytest.raises(ValueError, match="Cannot identify color"):
        Color("nope")


def test_usage_errors_are_not_color_errors():
    """Calling a helper wrongly is not a bad colour, and stays a plain error."""
    with pytest.raises(
        ValueError, match="At least two colours are required"
    ) as excinfo:
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

    def never_equal(_c1, _c2):
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


@pytest.mark.parametrize("space", ["lab", "oklab"])
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
    steps = [_oklab_distance(a, b) for a, b in pairwise(scale)]
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

    assert not all(a <= b for a, b in pairwise(hsl))
    assert hsl[3] > hsl[4]  # the dip
    assert all(a < b for a, b in pairwise(oklab))


@pytest.mark.parametrize(("start", "end"), [("red", "cyan"), ("black", "white")])
def test_oklab_steps_are_exactly_equal_inside_the_gamut(start, end):
    scale = color_scale((Color(start), Color(end)), 9, space="oklab")
    lightness = [c.oklab.lightness for c in scale]
    deltas = [b - a for a, b in pairwise(lightness)]
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


## Each grey is the last to clear its threshold against white, paired with the
## next one up. A threshold off by a level, or a `>` for a `>=`, moves one case.
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


def test_relative_steps_never_clip_and_land_exactly_on_the_limit():
    """The reason relative is the default: the step is a fraction of what is
    left, so it cannot overshoot and 1.0 reaches the end exactly."""
    for hex_value in ("#000000", "#808080", "#e0e0e0", "#ffffff"):
        color = Color(hex_value)
        assert color.lighten(1.0).lightness == 100.0
        assert color.darken(1.0).lightness == 0.0
        assert color.saturate(1.0).saturation == 100.0
        assert color.desaturate(1.0).saturation == 0.0
        for amount in (0.0, 0.1, 0.5, 0.9, 1.0):
            assert 0.0 <= color.lighten(amount).lightness <= 100.0
            assert 0.0 <= color.darken(amount).lightness <= 100.0


def test_absolute_steps_are_flat_and_clamp():
    """Absolute moves by the same amount wherever it starts, and stops at the
    end rather than running past it."""
    assert Color("#000000").lighten(0.1, relative=False).lightness == 10.0
    mid = Color("#808080")
    assert mid.lighten(0.1, relative=False).lightness == pytest.approx(
        mid.lightness + 10.0
    )
    assert Color("#e0e0e0").lighten(0.9, relative=False).lightness == 100.0
    assert Color("#202020").darken(0.9, relative=False).lightness == 0.0


def test_a_zero_step_changes_nothing():
    original = Color("#3d7ab8")
    for method in ("lighten", "darken", "saturate", "desaturate"):
        for relative in (True, False):
            assert getattr(original, method)(0.0, relative=relative) == original


@pytest.mark.parametrize("method", ["lighten", "darken", "saturate", "desaturate"])
@pytest.mark.parametrize("amount", [-0.1, 1.1, 2, -1])
def test_a_step_outside_the_unit_range_is_refused(method, amount):
    with pytest.raises(ValueError, match="must be between 0 and 1"):
        getattr(Color("red"), method)(amount)


def test_rotate_hue_wraps_in_both_directions():
    red = Color("red")
    assert red.rotate_hue(180) == Color("cyan")
    assert red.rotate_hue(-180) == Color("cyan")
    assert red.rotate_hue(360) == red
    assert red.rotate_hue(-360) == red
    assert red.rotate_hue(720) == red
    assert red.rotate_hue(120) == Color("lime")


def test_grayscale_keeps_the_luminance_and_desaturating_does_not():
    """The two greys are different, and the difference is the whole point.

    `desaturate(1.0)` holds HSL lightness, so every fully saturated colour
    collapses to the same mid grey whatever its brightness. `grayscale` holds
    luminance, so blue stays dark and yellow stays bright."""
    for name in ("blue", "yellow", "red", "lime"):
        color = Color(name)
        grey = color.grayscale()
        assert grey.relative_luminance == pytest.approx(
            color.relative_luminance, abs=1e-12
        )
        assert grey.red == grey.green == grey.blue
        assert color.desaturate(1.0).hex_l == "#7f7f7f"
    assert Color("blue").grayscale().hex_l == "#4c4c4c"
    assert Color("yellow").grayscale().hex_l == "#f7f7f7"


def test_greyscale_is_the_same_method():
    assert Color.greyscale is Color.grayscale
    assert Color("blue").greyscale() == Color("blue").grayscale()


def test_invert_is_its_own_inverse():
    for name in ("red", "black", "white", "#123456", "rebeccapurple"):
        color = Color(name)
        assert color.invert().invert() == color
    assert Color("black").invert() == Color("white")
    assert Color("red").invert() == Color("cyan")
    assert Color("#123456").invert().hex_l == "#edcba9"


def test_mix_reaches_both_endpoints_exactly():
    red, blue = Color("red"), Color("blue")
    for space in ("hsl", "lab", "lch", "oklab", "oklch"):
        assert red.mix(blue, 0.0, space=space) == red
        assert red.mix(blue, 1.0, space=space) == blue


def test_mix_defaults_to_oklab_and_takes_any_input_format():
    assert Color("red").mix("blue") == Color("red").mix("blue", space="oklab")
    assert Color("red").mix("blue") != Color("red").mix("blue", space="hsl")
    for other in ("blue", "#0000ff", (0, 0, 255), Color("blue")):
        assert Color("red").mix(other, 0.5) == Color("red").mix("blue", 0.5)


def test_mix_agrees_with_the_midpoint_of_a_three_step_scale():
    """`mix` and `color_scale` interpolate the same way, so they must agree
    where they overlap."""
    for space in ("hsl", "lab", "lch", "oklab", "oklch"):
        scale = color_scale((Color("red"), Color("blue")), 3, space=space)
        assert Color("red").mix("blue", 0.5, space=space) == scale[1]


def test_mix_takes_the_longer_arc_when_asked():
    assert Color("red").mix("blue", 0.5, space="hsl", longer=True) == Color("lime")
    with pytest.raises(ValueError, match="no hue channel"):
        Color("red").mix("blue", space="oklab", longer=True)


def test_mix_rejects_a_bad_amount_or_space():
    with pytest.raises(ValueError, match="must be between 0 and 1"):
        Color("red").mix("blue", 1.5)
    with pytest.raises(ValueError, match="Unknown interpolation space"):
        Color("red").mix("blue", space="nope")


def test_mix_blends_alpha_rather_than_carrying_it():
    """Unlike the single-colour adjustments, `mix` has two alphas to reconcile,
    so it interpolates between them the way it does every other channel."""
    clear, opaque = Color("red", alpha=0.0), Color("blue", alpha=1.0)
    assert [clear.mix(opaque, t).alpha for t in (0.0, 0.25, 0.5, 1.0)] == [
        0.0,
        0.25,
        0.5,
        1.0,
    ]
    assert (clear.alpha, opaque.alpha) == (0.0, 1.0)


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.lighten(0.3),
        lambda c: c.darken(0.3),
        lambda c: c.saturate(0.3),
        lambda c: c.desaturate(0.3),
        lambda c: c.rotate_hue(90),
        lambda c: c.grayscale(),
        lambda c: c.invert(),
    ],
)
def test_every_adjustment_carries_alpha_and_leaves_the_original_alone(call):
    """`mix` is deliberately absent: it blends alpha rather than carrying it,
    which is what test_mix_blends_alpha covers."""
    original = Color("#3d7ab8", alpha=0.4)
    before = original.hsl, original.alpha
    result = call(original)
    assert result is not original
    assert result.alpha == 0.4
    assert (original.hsl, original.alpha) == before


def test_is_dark_agrees_with_the_better_text_colour_everywhere():
    """The threshold is derived, not chosen: it is the luminance at which
    contrast against white equals contrast against black. So `is_dark` and
    `best_text_color` cannot disagree, and this asserts they do not."""
    for red in range(0, 256, 13):
        for green in range(0, 256, 17):
            for blue in range(0, 256, 19):
                color = Color(rgb=(red, green, blue))
                assert color.is_dark == (color.best_text_color() == Color("white"))
                assert color.is_light is not color.is_dark


def test_is_dark_at_the_obvious_ends():
    assert Color("black").is_dark is True
    assert Color("navy").is_dark is True
    assert Color("white").is_light is True
    assert Color("yellow").is_light is True


def test_complementary_is_half_a_turn():
    assert Color("red").complementary() == Color("cyan")
    assert Color("blue").complementary() == Color("yellow")
    assert Color("red").complementary().complementary() == Color("red")


def test_triadic_and_tetradic_are_evenly_spaced():
    triad = Color("red").triadic()
    assert [c.hue for c in triad] == [0.0, 120.0, 240.0]
    assert triad == (Color("red"), Color("lime"), Color("blue"))
    tetrad = Color("red").tetradic()
    assert [c.hue for c in tetrad] == [0.0, 90.0, 180.0, 270.0]


def test_analogous_sits_the_colour_between_its_neighbours():
    left, middle, right = Color("red").analogous(60)
    assert (left.hue, middle.hue, right.hue) == (300.0, 0.0, 60.0)
    assert middle == Color("red")
    assert Color("red").analogous()[0].hue == 330.0


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.complementary(),
        lambda c: c.analogous()[0],
        lambda c: c.triadic()[1],
        lambda c: c.tetradic()[2],
    ],
)
def test_harmonies_return_new_colours_and_carry_alpha(call):
    original = Color("#3d7ab8", alpha=0.4)
    result = call(original)
    assert result is not original
    assert result.alpha == 0.4
    assert original.hex_l == "#3d7ab8"


def test_repr_html_draws_the_colour():
    html = Color("red")._repr_html_()
    assert html.startswith("<div")
    assert html.endswith("</div>")
    assert "rgb(255 0 0)" in html
    assert ">red</span>" in html
    assert "linear-gradient" not in html


def test_repr_html_shows_alpha_over_a_checkerboard():
    """Otherwise a translucent colour would be composited onto whatever the
    notebook's background happens to be, and read as a different colour."""
    html = Color("red", alpha=0.5)._repr_html_()
    assert "rgb(255 0 0 / 0.5)" in html
    assert "linear-gradient" in html
    assert "red / 0.5" in html


def test_every_colour_input_has_a_converter():
    """The signature, the dispatch table and the alpha scales have to agree.

    They are three lists of the same formats, and nothing but this makes them
    match. Adding a keyword without a table entry used to be caught by an
    unreachable `else` at runtime, and only for the caller who tried it."""
    reserved = {"self", "color", "pick_for", "alpha", "picker", "pick_key", "equality"}
    parameters = inspect.signature(Color.__init__).parameters
    inputs = {
        name
        for name, parameter in parameters.items()
        if name not in reserved and parameter.kind is not parameter.VAR_KEYWORD
    }
    assert inputs == set(_KEYWORD_INPUTS)
    assert set(_KEYWORD_ALPHA_SCALES) == {"hsla", "rgba", "hslaf", "rgbaf"}
    assert set(_KEYWORD_ALPHA_SCALES) <= inputs


@pytest.mark.parametrize(
    ("build", "half", "opaque"),
    [
        (lambda a: Color(hsla=(0.0, 100.0, 50.0, a)), 50.0, 100.0),
        (lambda a: Color(rgba=(255.0, 0.0, 0.0, a)), 127.5, 255.0),
        (lambda a: Color(hslaf=(0.0, 1.0, 0.5, a)), 0.5, 1.0),
        (lambda a: Color(rgbaf=(1.0, 0.0, 0.0, a)), 0.5, 1.0),
    ],
    ids=["hsla", "rgba", "hslaf", "rgbaf"],
)
def test_every_alpha_carrying_input_reads_its_own_scale(build, half, opaque):
    """Each states its alpha on a different scale, so a table entry swapped
    between two of them would still produce a perfectly valid colour."""
    assert build(half).alpha == pytest.approx(0.5)
    assert build(opaque).alpha == 1.0


def test_the_one_input_rule_names_every_input():
    """The message is built from the same mapping the dispatch uses, so it
    cannot drift from the parameters it lists."""
    with pytest.raises(ValueError, match="Only one of") as excinfo:
        Color()
    message = str(excinfo.value)
    for name in ("color", "pick_for", *_KEYWORD_INPUTS):
        assert f"'{name}'" in message


def test_over_matches_the_porter_duff_formula():
    """Checked against the source-over definition written out separately,
    rather than against values this implementation produced."""
    for source_alpha in (0.0, 0.25, 0.5, 1.0):
        for backdrop_alpha in (0.0, 0.25, 0.5, 1.0):
            source = Color(rgbf=(1.0, 0.2, 0.0), alpha=source_alpha)
            backdrop = Color(rgbf=(0.0, 0.4, 1.0), alpha=backdrop_alpha)
            result = source.over(backdrop)
            alpha = source_alpha + backdrop_alpha * (1.0 - source_alpha)
            assert result.alpha == pytest.approx(alpha)
            if alpha == 0.0:
                continue
            for got, s, b in zip(result.rgbf, source.rgbf, backdrop.rgbf, strict=True):
                want = (
                    s * source_alpha + b * backdrop_alpha * (1.0 - source_alpha)
                ) / alpha
                assert got == pytest.approx(want, abs=1e-12)


def test_compositing_identities():
    red, blue, white = Color("red"), Color("blue"), Color("white")
    assert red.over(blue) == red  # an opaque source hides everything
    assert Color("red", alpha=0.0).over(blue) == blue  # and a clear one hides nothing
    assert Color("red", alpha=0.0).over(blue).alpha == 1.0
    assert Color("red", alpha=0.0).over(Color("blue", alpha=0.0)).alpha == 0.0
    assert red.over(white).alpha == 1.0


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("multiply", "#000000"),
        ("screen", "#ffffff"),
        ("darken", "#000000"),
        ("lighten", "#ffffff"),
        ("difference", "#ffffff"),
        ("exclusion", "#ffffff"),
    ],
)
def test_blend_modes_on_red_over_cyan(mode, expected):
    assert Color("red").blend(Color("cyan"), mode).hex_l == expected


@pytest.mark.parametrize("name", ["red", "#3d7ab8", "yellow", "black", "white"])
def test_the_blend_modes_with_an_identity_have_it(name):
    """multiply by white and screen with black both change nothing, which
    catches a formula with its operands the wrong way round."""
    color = Color(name)
    assert color.blend("white", "multiply") == color
    assert color.blend("black", "screen") == color
    assert color.blend("black", "lighten") == color
    assert color.blend("white", "darken") == color


def test_overlay_is_hard_light_with_the_operands_swapped():
    """That is how CSS defines it, and it is a property no coincidence
    satisfies: it has to hold for every pair."""
    for first in ("#3d7ab8", "red", "#202020", "#e0e0e0"):
        for second in ("#c08040", "cyan", "#101010", "#f0f0f0"):
            a, b = Color(first), Color(second)
            assert a.blend(b, "overlay") == b.blend(a, "hard-light")


## The three modes below come from https://www.w3.org/TR/compositing-1/. Each
## test states a consequence of the published formula -- a closed form it
## collapses to, an identity its prose asserts, or a branch its ordering
## decides -- rather than recording what this implementation returns.
_DODGE = _BLEND_MODES["color-dodge"]
_BURN = _BLEND_MODES["color-burn"]
_SOFT = _BLEND_MODES["soft-light"]
_CHANNELS = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]


@pytest.mark.parametrize("backdrop", _CHANNELS)
def test_dodging_with_black_changes_nothing(backdrop):
    """The spec's own words. Exact, because the formula divides by 1.0."""
    assert _DODGE(backdrop, 0.0) == backdrop


@pytest.mark.parametrize("backdrop", _CHANNELS)
def test_burning_with_white_changes_nothing(backdrop):
    """Also the spec's own words, but only to a rounding error: the formula is
    ``1 - min(1, (1 - Cb) / 1)``, and ``1 - (1 - 0.1)`` is not 0.1 in binary
    floating point. One ulp, and not worth deviating from the spec to remove.
    """
    assert _BURN(backdrop, 1.0) == pytest.approx(backdrop, abs=1e-15)


@pytest.mark.parametrize("backdrop", _CHANNELS)
def test_soft_light_at_a_half_source_is_the_backdrop(backdrop):
    """0.5 is the hinge between the two branches, and both reduce to Cb there,
    so this pins that the halves meet as well as the value."""
    assert _SOFT(backdrop, 0.5) == backdrop


@pytest.mark.parametrize("backdrop", _CHANNELS)
def test_soft_light_with_a_black_source_squares_the_backdrop(backdrop):
    """Cs = 0 makes the lower branch ``Cb - Cb(1 - Cb)``, which is Cb squared."""
    assert _SOFT(backdrop, 0.0) == pytest.approx(backdrop**2, abs=1e-15)


@pytest.mark.parametrize("backdrop", [0.3, 0.5, 0.81, 1.0])
def test_soft_light_with_a_white_source_is_the_spec_helper(backdrop):
    """Cs = 1 makes the upper branch exactly D(Cb), which is sqrt above 0.25."""
    assert _SOFT(backdrop, 1.0) == pytest.approx(math.sqrt(backdrop), abs=1e-15)


def test_the_soft_light_helper_has_no_seam_where_it_changes_definition():
    """D(Cb) is a cubic below 0.25 and sqrt above it, and the cubic's
    coefficients exist to make the two meet at 0.5. A transcription error in
    them would show as a step in the middle of a gradient."""
    assert _SOFT(0.25, 1.0) == pytest.approx(0.5, abs=1e-15)
    assert _SOFT(0.25 - 1e-9, 1.0) == pytest.approx(_SOFT(0.25 + 1e-9, 1.0), abs=1e-8)


def test_dodge_and_burn_resolve_their_overlapping_guards_the_spec_way():
    """Each has two guards that can be true at once, and the spec's ordering
    decides which. Nothing else distinguishes the two orderings, which is why
    these modes were left out until the spec could be read."""
    ## Cb == 0 is tested before Cs == 1, so a black backdrop wins over a
    ## white source and the answer is 0 rather than 1.
    assert _DODGE(0.0, 1.0) == 0.0
    ## Cb == 1 before Cs == 0: a white backdrop wins over a black source.
    assert _BURN(1.0, 0.0) == 1.0


def test_dodge_and_burn_clamp_instead_of_leaving_the_range():
    """Both formulas can exceed the range before the spec's min clamps them."""
    assert _DODGE(0.5, 0.75) == 1.0  ## 0.5 / 0.25 is 2
    assert _BURN(0.25, 0.5) == 0.0  ## 1 - min(1, 1.5)


@pytest.mark.parametrize("mode", ["color-dodge", "color-burn", "soft-light"])
def test_the_new_modes_rise_with_the_source(mode):
    """All three are non-decreasing in the source channel, which follows from
    the formulas and is the property a swapped branch tends to break."""
    blend = _BLEND_MODES[mode]
    grid = [i / 64 for i in range(65)]
    for backdrop in grid:
        seen = [blend(backdrop, source) for source in grid]
        assert seen == sorted(seen), f"{mode} falls back at backdrop {backdrop}"


def test_the_new_modes_have_their_identities_through_the_public_api():
    """The same identities as above, but reached the way a caller would --
    which also checks the operands are the way round CSS says.

    The soft-light source is built from ``rgbf`` rather than written as
    ``#808080``: a hex grey is 128/255, not a half, and at that source the
    channels come out 9.8e-4 away from the backdrop. ``==`` compares 8-bit
    values and would call that equal, so the hex version passes whether or not
    the formula is right.
    """
    half_grey = Color(rgbf=(0.5, 0.5, 0.5))
    for name in ("red", "#3d7ab8", "yellow", "black", "white"):
        color = Color(name)
        assert Color("black").blend(color, "color-dodge") == color
        assert Color("white").blend(color, "color-burn") == color
        blended = half_grey.blend(color, "soft-light")
        assert blended == color
        ## Exactly, not merely to the nearest 8-bit value.
        for got, want in zip(blended.rgbf, color.rgbf, strict=True):
            assert got == want


## The four non-separable modes, from https://www.w3.org/TR/compositing-1/
## section 10.2. They are defined through Lum, Sat, SetLum and SetSat, and the
## tests below state consequences of those definitions rather than recording
## what this implementation returns.
_HUE = _NONSEPARABLE_BLEND_MODES["hue"]
_SATURATION = _NONSEPARABLE_BLEND_MODES["saturation"]
_COLOR = _NONSEPARABLE_BLEND_MODES["color"]
_LUMINOSITY = _NONSEPARABLE_BLEND_MODES["luminosity"]
_TRIPLES = [
    (0.0, 0.0, 0.0),
    (1.0, 1.0, 1.0),
    (1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.24, 0.48, 0.72),
    (0.9, 0.85, 0.1),
    (0.5, 0.5, 0.5),
]


def test_the_blend_luma_is_not_wcag_relative_luminance():
    """Two different weightings, and using the wrong one would darken or
    lighten every non-separable blend by a plausible-looking amount rather
    than raising. The spec's are 0.3/0.59/0.11 on the channels as they stand;
    WCAG's are 0.2126/0.7152/0.0722 on linearised ones.
    """
    assert _blend_luma((1.0, 0.0, 0.0)) == 0.3
    assert _blend_luma((0.0, 1.0, 0.0)) == 0.59
    assert _blend_luma((0.0, 0.0, 1.0)) == 0.11
    ## The weights summing to exactly 1.0 is what makes SetLum exact.
    assert _blend_luma((1.0, 1.0, 1.0)) == 1.0
    ## And they really are a different answer from the WCAG pair.
    assert _blend_luma((0.0, 1.0, 0.0)) != rgb2relative_luminance((0.0, 255.0, 0.0))


@pytest.mark.parametrize("triple", _TRIPLES)
def test_a_non_separable_blend_with_itself_changes_nothing(triple):
    """Each mode takes some of hue, saturation and luma from one operand and
    the rest from the other, so with one colour on both sides every part comes
    from the same place and the colour has to survive. Exact to a rounding
    error, because the luma weights sum to 1."""
    for blend in (_HUE, _SATURATION, _COLOR, _LUMINOSITY):
        for got, want in zip(blend(triple, triple), triple, strict=True):
            assert got == pytest.approx(want, abs=1e-15)


@pytest.mark.parametrize("backdrop", _TRIPLES)
@pytest.mark.parametrize("source", _TRIPLES)
def test_the_non_separable_modes_keep_the_luma_they_claim_to(backdrop, source):
    """Three of the four are defined to keep the backdrop's luma and the
    fourth to take the source's. SetLum makes that exact, and ClipColor is
    built to preserve it too -- which is the whole reason it scales about the
    luma instead of clamping each channel."""
    for blend in (_HUE, _SATURATION, _COLOR):
        assert _blend_luma(blend(backdrop, source)) == pytest.approx(
            _blend_luma(backdrop), abs=1e-15
        )
    assert _blend_luma(_LUMINOSITY(backdrop, source)) == pytest.approx(
        _blend_luma(source), abs=1e-15
    )


@pytest.mark.parametrize("backdrop", _TRIPLES)
@pytest.mark.parametrize("source", _TRIPLES)
def test_luminosity_is_color_with_the_operands_swapped(backdrop, source):
    """The spec calls luminosity "an inverse effect to that of the Color
    mode"; the formulas say precisely this. Exact, not approximate, since both
    reduce to the same SetLum call."""
    assert _LUMINOSITY(backdrop, source) == _COLOR(source, backdrop)


@pytest.mark.parametrize("grey", [0.0, 0.2, 0.5, 0.8, 1.0])
@pytest.mark.parametrize("source", _TRIPLES)
def test_saturation_over_a_grey_backdrop_changes_nothing(grey, source):
    """The spec's own words: "Painting with this mode in an area of the
    backdrop that is a pure gray (no saturation) produces no change." It falls
    out of SetSat, which sends a colour with no spread to black, and the SetLum
    that follows lifting it back."""
    backdrop = (grey, grey, grey)
    for got in _SATURATION(backdrop, source):
        assert got == pytest.approx(grey, abs=1e-15)


@pytest.mark.parametrize("backdrop", _TRIPLES)
@pytest.mark.parametrize("grey", [0.0, 0.3, 1.0])
def test_hue_from_a_grey_source_is_grey(backdrop, grey):
    """A grey has no hue to borrow. SetSat gives black, so the result is the
    backdrop's luma with nothing else -- grey at that lightness."""
    result = _HUE(backdrop, (grey, grey, grey))
    assert result[0] == pytest.approx(result[1], abs=1e-15)
    assert result[1] == pytest.approx(result[2], abs=1e-15)
    assert _blend_luma(result) == pytest.approx(_blend_luma(backdrop), abs=1e-15)


## Pairs where the two operands have different saturations and nothing needs
## clipping, so "whose saturation is it" has an observable answer.
_DIFFERENT_SATURATIONS = [
    ((0.24, 0.48, 0.72), (0.35, 0.6, 0.45)),
    ((0.4, 0.5, 0.6), (0.2, 0.8, 0.5)),
    ((0.9, 0.85, 0.8), (0.55, 0.75, 0.65)),
]


@pytest.mark.parametrize(("backdrop", "source"), _DIFFERENT_SATURATIONS)
def test_hue_keeps_the_backdrop_saturation_not_the_source_one(backdrop, source):
    """``SetSat(Cs, Sat(Cb))`` -- the source contributes its hue and the
    backdrop its saturation. Reading Sat from the wrong operand passes every
    other test here, including the luma and self-blend ones, because it only
    changes how far the result sits from grey."""
    assert _blend_saturation(backdrop) != pytest.approx(_blend_saturation(source))
    result = _HUE(backdrop, source)
    assert _blend_saturation(result) == pytest.approx(
        _blend_saturation(backdrop), abs=1e-15
    )


@pytest.mark.parametrize(("backdrop", "source"), _DIFFERENT_SATURATIONS)
def test_saturation_mode_takes_the_source_saturation(backdrop, source):
    """The mirror of the above: ``SetSat(Cb, Sat(Cs))``."""
    result = _SATURATION(backdrop, source)
    assert _blend_saturation(result) == pytest.approx(
        _blend_saturation(source), abs=1e-15
    )


@pytest.mark.parametrize("requested", [0.0, 0.3, 1.0])
def test_setting_the_saturation_of_a_flat_colour_gives_black(requested):
    """The spec sets all three channels to zero when there is no spread to
    rescale, whatever saturation was asked for.

    Tested here rather than through a blend mode because it cannot be seen
    from there: every use of SetSat is followed by a SetLum, which shifts all
    three channels equally, so returning the input unchanged instead of zero
    produces exactly the same colour. This pins the spec's literal behaviour.
    """
    assert _set_blend_saturation((0.4, 0.4, 0.4), requested) == (0.0, 0.0, 0.0)
    assert _set_blend_saturation((0.0, 0.0, 0.0), requested) == (0.0, 0.0, 0.0)


def test_clipping_scales_about_the_luma_rather_than_clamping():
    """ClipColor's job. Clamping each channel would move the luma, which is
    what the mode promised not to do, so it scales the spread about the luma
    instead -- costing saturation and keeping lightness.

    Both branches are reached: a bright source under a dark backdrop pushes
    channels below zero, and a dark source under a bright one pushes them
    above one.
    """
    vivid = (0.0, 0.0, 1.0)
    dark, bright = (0.02, 0.02, 0.02), (0.98, 0.98, 0.98)

    low = _COLOR(dark, vivid)
    assert min(low) >= 0.0
    assert _blend_luma(low) == pytest.approx(_blend_luma(dark), abs=1e-15)
    assert _blend_saturation(low) < _blend_saturation(vivid)

    high = _COLOR(bright, vivid)
    assert max(high) <= 1.0
    assert _blend_luma(high) == pytest.approx(_blend_luma(bright), abs=1e-15)
    assert _blend_saturation(high) < _blend_saturation(vivid)


def test_an_in_range_blend_needs_no_clipping():
    """The other side of both branches, so neither is only ever taken."""
    unclipped = _COLOR((0.5, 0.5, 0.5), (0.4, 0.5, 0.6))
    assert min(unclipped) >= 0.0
    assert max(unclipped) <= 1.0
    assert _blend_saturation(unclipped) == pytest.approx(
        _blend_saturation((0.4, 0.5, 0.6)), abs=1e-15
    )


def test_the_non_separable_modes_work_through_the_public_api():
    """Reached the way a caller would, which also checks the operands are the
    way round CSS says: this colour is the source, the argument the backdrop.
    """
    for first in ("#3d7ab8", "red", "#202020", "#e0e0e0"):
        for second in ("#c08040", "cyan", "white", "black"):
            source, backdrop = Color(first), Color(second)
            assert source.blend(backdrop, "luminosity") == backdrop.blend(
                source, "color"
            )
        assert Color(first).blend(first, "hue") == Color(first)
        assert Color(first).blend(first, "luminosity") == Color(first)


def test_a_blend_mode_may_be_spelled_with_an_underscore():
    a, b = Color("#3d7ab8"), Color("#c08040")
    assert a.blend(b, "hard_light") == a.blend(b, "hard-light")
    assert a.blend(b, "HARD-LIGHT") == a.blend(b, "hard-light")


def test_normal_is_what_over_does():
    source, backdrop = Color("red", alpha=0.4), Color("blue", alpha=0.6)
    assert source.blend(backdrop, "normal") == source.over(backdrop)
    assert source.blend(backdrop).alpha == source.over(backdrop).alpha


def test_linear_compositing_is_a_different_answer_on_purpose():
    """Sixty channel steps apart, which is why it is a flag and not a
    detail: encoded is what a browser shows, linear is the physical one."""
    encoded = Color("red", alpha=0.5).over("white")
    linear = Color("red", alpha=0.5).over("white", linear=True)
    assert encoded.green == pytest.approx(127.5)
    assert linear.green == pytest.approx(187.516, abs=0.001)
    assert encoded.alpha == linear.alpha == 1.0


def test_blend_rejects_a_mode_it_does_not_have():
    """CSS has sixteen and this has all sixteen, so what is left to reject is
    everything else -- including the names of things that sound like modes."""
    for mode in ("nonsense", "plus-lighter", "dissolve", "divide", "", "hue "):
        with pytest.raises(ValueError, match="Unknown blend mode"):
            Color("red").blend("blue", mode)


def test_every_css_blend_mode_is_present():
    """Guard the guard: the rejection test above only means something if the
    sixteen really are all here."""
    assert {
        "normal",
        "multiply",
        "screen",
        "overlay",
        "darken",
        "lighten",
        "color-dodge",
        "color-burn",
        "hard-light",
        "soft-light",
        "difference",
        "exclusion",
        "hue",
        "saturation",
        "color",
        "luminosity",
    } == _ALL_BLEND_MODES


@pytest.mark.parametrize("mode", sorted(_ALL_BLEND_MODES))
def test_every_blend_stays_in_range_and_leaves_its_operands_alone(mode):
    source = Color("#3d7ab8", alpha=0.4)
    backdrop = Color("#c08040", alpha=0.7)
    before = (source.hsl, source.alpha, backdrop.hsl, backdrop.alpha)
    result = source.blend(backdrop, mode)
    assert all(0.0 <= channel <= 1.0 for channel in result.rgbf)
    assert 0.0 <= result.alpha <= 1.0
    assert (source.hsl, source.alpha, backdrop.hsl, backdrop.alpha) == before
    assert result is not source
    assert result is not backdrop


## `a` and `c` carry a strategy stricter than the hash, `b` a looser one, and
## all three render the same hex. That is the arrangement in which `==` misbehaves.
def _mixed_strategy_trio():
    return (
        Color(hsl=(0, 100, 50.0000001), equality=HSL_equivalence),
        Color(hsl=(0, 100, 50), equality=RGB_equivalence),
        Color(hsl=(0, 100, 50.0000002), equality=HSL_equivalence),
    )


def test_equality_is_not_transitive_across_mixed_strategies():
    """Documented rather than fixed: `==` consults both operands, so a loose
    strategy on one of them satisfies the `or` for every pair it touches."""
    a, b, c = _mixed_strategy_trio()
    assert a == b
    assert b == c
    assert a != c


def test_a_strict_strategy_is_unenforceable_through_the_operator():
    a, b, _ = _mixed_strategy_trio()
    assert a == b  # the loose strategy on b decides it
    assert not a.equals(b, HSL_equivalence)  # naming one does not


def test_equals_is_reflexive_symmetric_and_transitive():
    """The property `==` lacks. One strategy is applied to both operands, so
    whatever holds for the strategy holds for the comparison."""
    a, b, c = _mixed_strategy_trio()
    for equality in (RGB_equivalence, HSL_equivalence):
        for first in (a, b, c):
            assert first.equals(first, equality)
        for first, second in ((a, b), (b, c), (a, c), (b, a), (c, b), (c, a)):
            assert first.equals(second, equality) == second.equals(first, equality)
        if a.equals(b, equality) and b.equals(c, equality):
            assert a.equals(c, equality)


def test_equals_ignores_what_the_operands_carry():
    a, b, _ = _mixed_strategy_trio()
    assert a.equals(b) == b.equals(a)
    assert a.equals(b, HSL_equivalence) == b.equals(a, HSL_equivalence)
    ## a carries HSL_equivalence, and equals does not consult it.
    assert a.equals(b) is True


def test_equals_takes_any_input_format():
    red = Color("red")
    assert red.equals("red")
    assert red.equals("#f00")
    assert red.equals("rgb(255 0 0)")
    assert red.equals(Color("red"))
    assert not red.equals("blue")


def test_a_strategy_stricter_than_the_hash_is_only_a_collision():
    """Not a contract violation. Python requires that equal objects hash
    equal, not the converse, so `set` and `dict` resolve this by comparing."""
    a, _, c = _mixed_strategy_trio()
    assert hash(a) == hash(c)
    assert a != c
    assert len({a, c}) == 2
    assert len({a: 1, c: 2}) == 2


def test_a_strategy_looser_than_the_hash_does_break_the_contract():
    """This is the direction that bites, and it needs a custom strategy:
    neither built-in is looser than `hex_l`."""

    def same_hue(first, second):
        return round(first.hue) == round(second.hue)

    bright = Color("#ff0000", equality=same_hue)
    dark = Color("#7f0000", equality=same_hue)
    assert bright == dark
    assert hash(bright) != hash(dark)
    assert dark not in {bright}  # despite comparing equal


def _picked_in_a_fresh_process(expression):
    """Pick a colour in a separate interpreter, so hash salting is re-rolled."""
    ## No shell, and the argv is built here out of sys.executable and
    ## literals from the parametrize list.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-c",
            "from colourings import Color\n"
            "from colourings.colour import hash_or_str, stable_key\n"
            f"print({expression})\n",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.parametrize(
    "expression",
    [
        'Color(pick_for="user:123").hex_l',
        "Color(pick_for=42).hex_l",
        "Color(pick_for=[1, 2]).hex_l",
        'Color(pick_for=("a", "b")).hex_l',
        'Color(pick_for={"a": 1}).hex_l',
    ],
)
def test_pick_for_is_stable_across_processes(expression):
    """The point of the default key. Run in subprocesses because the salt that
    used to break this is only re-rolled by a new interpreter."""
    first = _picked_in_a_fresh_process(expression)
    assert first == _picked_in_a_fresh_process(expression)
    ## The expression comes from the parametrize list a few lines up, and
    ## calls into colourings, so literal_eval cannot evaluate it.
    assert first == str(eval(expression))  # noqa: S307


def test_hash_or_str_is_still_per_process():
    """Kept, and kept honest: it is the reason the default had to change."""
    expression = 'Color(pick_for="user:123", pick_key=hash_or_str).hex_l'
    runs = {_picked_in_a_fresh_process(expression) for _ in range(4)}
    assert len(runs) > 1


def test_the_old_default_was_stable_only_for_unhashable_keys():
    """Which is the finding that settled this: whether a caller got a stable
    colour depended on whether their key happened to be hashable."""
    assert isinstance(hash_or_str([1, 2]), str)  # the stable fallback
    assert isinstance(hash_or_str("hello"), int)  # the salted path
    assert isinstance(hash_or_str(42), int)


def test_stable_key_distinguishes_type_from_value():
    assert stable_key("user:123") == "struser:123"
    assert stable_key([1, 2]) == "list[1, 2]"
    assert stable_key(1) != stable_key("1")
    assert stable_key(1) != stable_key(1.0)


def test_stable_key_matches_the_old_fallback_for_unhashable_keys():
    """Why the pinned list colours in this file did not have to change."""
    for value in ([1, 2], {"a": 1}, {1, 2}):
        assert stable_key(value) == hash_or_str(value)


def test_picking_no_longer_quantises_through_a_string():
    """The picked colour used to be routed through `.web`, costing it every
    bit of precision below 8 per channel."""
    picked = Color(pick_for="user:123")
    direct = RGB_color_picker(stable_key("user:123"))
    assert picked.hsl == direct.hsl
    assert picked.rgbf == direct.rgbf


def test_colour_is_the_same_class_as_color():
    """It was a subclass, and that leaked: `Colour is Color` was False, the
    repr said `<Color ...>` anyway, and every constructor handed back a Color,
    so a Colour stopped being one the moment it went through a scale."""
    assert Colour is Color
    assert type(Colour("red")) is Color
    assert repr(Colour("red")) == "<Color red>"
    assert isinstance(Color("red"), Colour)
    assert isinstance(Colour("red"), Color)


def test_a_colour_survives_the_operations_that_used_to_demote_it():
    scaled = color_scale([Colour("red"), Colour("blue")], 3)
    assert all(isinstance(c, Colour) for c in scaled)
    assert isinstance(next(Colour("red").range_to("blue", 3)), Colour)
    assert isinstance(Colour("red").lighten(), Colour)
    assert isinstance(Colour("red").mix("blue"), Colour)


def test_subclassing_still_works_through_the_alias():
    class Tint(Colour):
        pass

    assert Tint("red").hsl == (0.0, 100.0, 50.0)
    assert isinstance(Tint("red"), Color)


@pytest.mark.parametrize(
    ("old", "new"),
    [("HSL", NAMED_HSL), ("RGB", NAMED_RGB), ("HEX", NAMED_HEX)],
)
def test_the_pre_2_0_accessor_names_still_work_and_say_so(old, new):
    """A rename that fails loudly. Reached through the module `__getattr__`
    rather than left as a global, so the old name cannot be quietly served the
    tuple type of the same name from `definitions`."""
    import colourings.colour

    with pytest.warns(DeprecationWarning, match=f"{old} was renamed"):
        assert getattr(colourings.colour, old) is new


def test_the_deprecation_message_names_the_replacement():
    import colourings.colour

    with pytest.warns(DeprecationWarning, match="NAMED_HSL") as record:
        _ = colourings.colour.HSL
    assert "shadowed" in str(record[0].message)
    with pytest.warns(DeprecationWarning, match="NAMED_HEX") as record:
        _ = colourings.colour.HEX
    ## HEX never shadowed anything; only HSL and RGB did.
    assert "shadowed" not in str(record[0].message)


def test_an_unknown_module_attribute_still_raises():
    import colourings.colour

    with pytest.raises(AttributeError, match="has no attribute 'nope'"):
        _ = colourings.colour.nope


@pytest.mark.parametrize(
    ("accessor", "expected"),
    [(NAMED_HSL, "C_HSL"), (NAMED_RGB, "C_RGB"), (NAMED_HEX, "C_HEX")],
)
def test_each_accessor_names_itself_in_its_error(accessor, expected):
    """`NAMED_RGB` and `NAMED_HEX` look their colours up through `NAMED_HSL`,
    so all three used to report `C_HSL` — a typo on one was blamed on another.
    The message also follows Python's own wording now."""
    with pytest.raises(AttributeError, match=f"'{expected}' object has no attribute"):
        getattr(accessor, "NOSUCHCOLOUR")  # noqa: B009


@pytest.mark.parametrize("accessor", [NAMED_HSL, NAMED_RGB, NAMED_HEX])
def test_the_accessors_are_case_insensitive(accessor):
    assert getattr(accessor, "BLUE") == getattr(accessor, "blue")  # noqa: B009
    assert getattr(accessor, "RebeccaPurple") == getattr(accessor, "rebeccapurple")  # noqa: B009
