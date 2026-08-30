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


def test_alpha_entered_twice():
    c = Color(rgba=(1, 1, 1, 255), alpha=1)
    assert c.alpha == 1
    Color(rgbaf=(1, 1, 1, 1), alpha=1)
    assert c.alpha == 1
    Color(hsla=(1, 1, 1, 1), alpha=1)
    assert c.alpha == 1


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


def test_unsupported_hsv_input_hits_constructor_error_path():
    with pytest.raises(ValueError, match="Input not recognised"):
        Color(hsv=(120, 50, 50))


def test_colour():
    assert Colour("red") == Color("red")


def test_only_one_input():
    with pytest.raises(ValueError):
        Color(color="red", pick_for="foo")


@pytest.mark.xfail(strict=False)
def test_pick_for():
    foo = object()
    bar = object()
    assert Color(pick_for=foo) == Color(pick_for=foo)
    assert Color(pick_for=foo) != Color(pick_for=bar)


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
        lambda: Color(hsv=(0, 1, 1)),
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
    with pytest.raises(UnknownColorError):
        Color(hsv=(0, 1, 1))
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
