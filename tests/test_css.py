"""Reading and writing CSS color syntax."""

import pytest

from colourings import Color
from colourings.conversions import hex2rgba, rgba2hex
from colourings.css import (
    CSS_FUNCTION_NAMES,
    LINEAR_P3_TO_LINEAR_SRGB,
    XYZ_D65_TO_LINEAR_SRGB,
    css2hsl,
    css2hsla,
    hsla2css,
    is_css,
)
from colourings.errors import InvalidColorError, UnknownColorError


@pytest.mark.parametrize(
    "text",
    [
        "rgb(255, 0, 0)",  # legacy commas
        "rgb(255 0 0)",  # CSS Color 4 spacing
        "rgb(100% 0% 0%)",  # percentages
        "RGB(255 0 0)",  # case
        "  rgb(255 0 0)  ",  # surrounding space
        "hsl(0, 100%, 50%)",
        "hsl(0 100% 50%)",
        "hsl(0deg 100% 50%)",
        "hsl(1turn 100% 50%)",
        "hsl(0 100 50)",  # bare numbers where CSS allows either
        "hsl(-360 100% 50%)",  # a hue outside one turn wraps
        "oklch(0.62796 0.25768 29.23389)",
        "oklab(0.62796 0.22486 0.12585)",
        "lab(53.2408 80.0925 67.2032)",
        "lch(53.2408 104.5518 40)",
    ],
)
def test_every_spelling_of_red_reads_as_red(text):
    assert Color(text) == Color("red")


def test_alpha_is_read_from_either_position():
    """CSS writes the alpha after a slash; the older rgba() form puts it last.
    Both spellings appear in the wild and both are accepted."""
    for text in (
        "rgba(255, 0, 0, 0.5)",
        "rgb(255 0 0 / 0.5)",
        "rgb(255, 0, 0, 0.5)",
        "rgb(255 0 0 / 50%)",
        "hsla(0, 100%, 50%, 0.5)",
        "hsl(0 100% 50% / 0.5)",
    ):
        color = Color(text)
        assert color == Color("red")
        assert color.alpha == 0.5


@pytest.mark.parametrize(
    ("text", "degrees"),
    [
        ("hsl(180 100% 50%)", 180.0),
        ("hsl(180deg 100% 50%)", 180.0),
        ("hsl(0.5turn 100% 50%)", 180.0),
        ("hsl(200grad 100% 50%)", 180.0),
        ("hsl(-180 100% 50%)", 180.0),
        ("hsl(540 100% 50%)", 180.0),
    ],
)
def test_hue_is_read_in_any_angle_unit_and_wrapped(text, degrees):
    assert Color(text).hue == pytest.approx(degrees, abs=1e-6)


def test_transparent_is_black_with_no_alpha():
    color = Color("transparent")
    assert color.alpha == 0.0
    assert color.rgb == (0.0, 0.0, 0.0)
    assert Color("  TRANSPARENT  ") == color


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("rgb(300 0 0)", "not an RGB type"),
        ("rgb(255 0)", "takes 3 components"),
        ("rgb(1 2 3 4 5)", "takes 3 components"),
        ("rgb(a b c)", "Expected a number"),
        ("hsl(zzz 100% 50%)", "Expected an angle"),
        ("hsl(0 100% 50% / 2)", "Alpha must be between 0 and 1"),
    ],
)
def test_a_css_function_that_cannot_be_read_says_why(text, message):
    """`is_css` matches on shape, so a malformed function reaches the parser
    and gets a specific complaint rather than "cannot identify color"."""
    assert is_css(text)
    with pytest.raises(InvalidColorError, match=message):
        Color(text)


def test_out_of_range_is_refused_rather_than_clamped():
    """A browser reads rgb(300 0 0) as red. Quietly turning one colour into
    another is what this library avoids, so it raises instead."""
    with pytest.raises(InvalidColorError):
        Color("rgb(300 0 0)")
    with pytest.raises(InvalidColorError):
        Color("rgb(-1 0 0)")


## CSS Color 4 gives each of these axes its own percentage reference, so a
## percentage is only meaningful against the right one. Each pair is a
## percentage and the number it stands for, and every value is inside the sRGB
## gamut on purpose: out of gamut both sides clip, and a wrong reference would
## be hidden by the two of them landing on the same gamut boundary.
PERCENTAGE_EQUIVALENTS = [
    ("lab(50 20% 0)", "lab(50 25 0)"),  ## a: 100% = 125
    ("lab(50 -20% 0)", "lab(50 -25 0)"),  ## and -100% = -125
    ("lab(50 0 20%)", "lab(50 0 25)"),  ## b: the same reference as a
    ("lch(50 20% 200)", "lch(50 30 200)"),  ## C: 100% = 150
    ("oklab(0.5 25% 0)", "oklab(0.5 0.1 0)"),  ## a: 100% = 0.4
    ("oklab(0.5 0 25%)", "oklab(0.5 0 0.1)"),  ## b: the same reference as a
    ("oklch(0.6 25% 200)", "oklch(0.6 0.1 200)"),  ## C: 100% = 0.4
]


@pytest.mark.parametrize(("percentage", "number"), PERCENTAGE_EQUIVALENTS)
def test_a_percentage_means_the_number_the_spec_says_it_does(percentage, number):
    """A wrong reference misreads a colour rather than rejecting it, which is
    why these axes took numbers only until the references could be read from
    the specification."""
    assert Color(percentage) == Color(number)


@pytest.mark.parametrize(
    ("percentage", "number"),
    [
        ("oklch(0.5 150% 200)", "oklch(0.5 0.6 200)"),
        ("lab(50 200% 0)", "lab(50 250 0)"),
        ("lch(50 120% 200)", "lch(50 180 200)"),
    ],
)
def test_a_percentage_over_one_hundred_is_refused_like_its_number(percentage, number):
    """100% is the reference, not a maximum, so the percentage is pure
    notation: past the axis's declared range it is refused exactly as the
    number is. Refused rather than clipped, for the same reason
    ``rgb(300 0 0)`` is."""
    with pytest.raises(InvalidColorError) as from_percentage:
        Color(percentage)
    with pytest.raises(InvalidColorError) as from_number:
        Color(number)
    assert str(from_percentage.value) == str(from_number.value)


def test_is_css_matches_only_what_this_module_reads():
    assert is_css("rgb(1 2 3)")
    assert is_css("transparent")
    assert is_css("OKLCH(0.5 0.1 200)")
    assert not is_css("#ff0000")
    assert not is_css("red")
    assert not is_css("colour(1 2 3)")
    assert not is_css("rgb(1 2 3")
    assert not is_css(("rgb", 1, 2, 3))
    assert not is_css(None)


def test_css2hsl_drops_the_alpha_that_css2hsla_keeps():
    assert css2hsla("rgb(255 0 0 / 0.25)").alpha == 25.0
    assert css2hsl("rgb(255 0 0 / 0.25)") == (0.0, 100.0, 50.0)
    assert len(css2hsl("rgb(255 0 0)")) == 3


@pytest.mark.parametrize(
    ("text", "rgba"),
    [
        ("#ff000080", (255.0, 0.0, 0.0, 128.0)),
        ("#f008", (255.0, 0.0, 0.0, 136.0)),
        ("#00000000", (0.0, 0.0, 0.0, 0.0)),
        ("#FFFFFFFF", (255.0, 255.0, 255.0, 255.0)),
    ],
)
def test_hex_with_alpha_is_read(text, rgba):
    assert hex2rgba(text) == rgba
    assert Color(text).alpha == pytest.approx(rgba[3] / 255.0)


@pytest.mark.parametrize("text", ["#ff0000", "#f00", "#ff00000", "#nothex", "ff000080"])
def test_hex2rgba_rejects_anything_that_is_not_hex_with_alpha(text):
    """The 3- and 6-digit forms carry no alpha and belong to hex2rgb."""
    with pytest.raises(InvalidColorError, match="hexadecimal with alpha"):
        hex2rgba(text)


def test_rgba2hex_shortens_only_when_it_can():
    assert rgba2hex((255, 0, 0, 128)) == "#ff000080"
    assert rgba2hex((255, 0, 0, 136)) == "#f008"
    assert rgba2hex((255, 0, 0, 136), force_long=True) == "#ff000088"
    with pytest.raises(InvalidColorError, match="not of RGBA type"):
        rgba2hex((255, 0, 0, 300))


def test_whitespace_around_any_string_form_is_ignored():
    for text in (" red ", "  #ff0000  ", "\tRED\n", " rgb(255 0 0) "):
        assert Color(text) == Color("red")
    assert Color(web=" red ") == Color("red")


def test_an_alpha_given_twice_must_agree():
    assert Color("#ff000080", alpha=128 / 255).alpha == pytest.approx(128 / 255)
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color("#ff000080", alpha=0.1)
    assert Color("rgb(255 0 0 / 0.5)", alpha=0.5).alpha == 0.5
    with pytest.raises(ValueError, match="Alpha value defined twice"):
        Color("rgb(255 0 0 / 0.5)", alpha=0.1)


@pytest.mark.parametrize(
    ("form", "opaque", "translucent"),
    [
        ("hex", "#f00", "#ff00007f"),
        ("rgb", "rgb(255 0 0)", "rgb(255 0 0 / 0.5)"),
        ("hsl", "hsl(0 100% 50%)", "hsl(0 100% 50% / 0.5)"),
        ("oklch", "oklch(0.62796 0.25768 29.23389)", None),
    ],
)
def test_to_css_writes_each_form_and_adds_alpha_only_when_needed(
    form, opaque, translucent
):
    assert Color("red").to_css(form) == opaque
    if translucent is not None:
        assert Color("red", alpha=0.5).to_css(form) == translucent


def test_to_css_rejects_a_form_it_does_not_write():
    with pytest.raises(ValueError, match="Unknown CSS form"):
        Color("red").to_css("cmyk")


def test_every_form_round_trips_exactly():
    """The precision each form is written to is chosen so that reading it back
    gives the same 8-bit colour. It is not free: oklch needs five decimals,
    because its chroma axis is only 0.4 wide and three decimals moved colours
    by up to five channel steps."""
    for red in range(0, 256, 37):
        for green in range(0, 256, 41):
            for blue in range(0, 256, 43):
                for alpha in (1.0, 0.5, 0.0, 64 / 255):
                    color = Color(rgb=(red, green, blue), alpha=alpha)
                    for form in ("hex", "rgb", "hsl", "oklch"):
                        back = Color(color.to_css(form))
                        assert back.hex_l == color.hex_l, (form, color.to_css(form))
                        assert back.alpha == pytest.approx(alpha, abs=0.002)


def test_a_whole_channel_is_not_trimmed_away():
    """`250` must not be written as `25`. Stripping trailing zeros from the
    integer part turns a rounding into a different colour."""
    assert Color(rgb=(250, 200, 100)).to_css("rgb") == "rgb(250 200 100)"
    assert Color("black").to_css("rgb") == "rgb(0 0 0)"


def test_hsla2css_is_usable_without_a_color():
    assert hsla2css((0, 100, 50)) == "#f00"
    assert hsla2css((0, 100, 50), 0.5, "rgb") == "rgb(255 0 0 / 0.5)"


def test_css2hsla_refuses_a_string_that_is_not_a_color_function():
    """Reachable by calling the parser directly; `Color` gates on `is_css`."""
    for text in ("nope", "#ff0000", "rgb(1 2 3", "colour(1 2 3)"):
        with pytest.raises(InvalidColorError, match="Not a CSS color function"):
            css2hsla(text)


def test_hsl_components_outside_their_range_are_refused():
    """hsl() is the one function whose components are already in the library's
    own units, so nothing downstream range-checks them for it."""
    for text in ("hsl(0 200% 50%)", "hsl(0 100% 150%)", "hsl(0 -10% 50%)"):
        with pytest.raises(InvalidColorError, match="not an HSL type"):
            Color(text)


## --- color() and the predefined spaces --------------------------------------


def _rgb_to_xyz_from_chromaticities(primaries, white):
    """Derive a linear-RGB to XYZ matrix from primaries and a white point.

    The textbook construction: each primary as an XYZ direction, scaled so
    that the three together send white to the white point. Written out here so
    that the matrix in the package has a second, independent source -- rather
    than being trusted because it was copied carefully.
    """

    def direction(x, y):
        return (x / y, 1.0, (1.0 - x - y) / y)

    def determinant(rows):
        return (
            rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
            - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
            + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0])
        )

    columns = [direction(*primary) for primary in primaries]
    target = direction(*white)
    base = [[columns[j][i] for j in range(3)] for i in range(3)]
    whole = determinant(base)
    scales = []
    for index in range(3):
        replaced = [row[:] for row in base]
        for row in range(3):
            replaced[row][index] = target[row]
        scales.append(determinant(replaced) / whole)
    return [[columns[j][i] * scales[j] for j in range(3)] for i in range(3)]


def test_the_display_p3_matrix_agrees_with_its_own_chromaticities():
    """The constant in the package is the product of two matrices copied from
    CSS Color 4's sample code. This derives the first of them from the
    published Display P3 primaries and D65 instead, which is a different route
    to the same number -- and they agree to machine precision.
    """
    derived = _rgb_to_xyz_from_chromaticities(
        [(0.680, 0.320), (0.265, 0.690), (0.150, 0.060)], (0.3127, 0.3290)
    )
    ## The specification's `lin_P3_to_XYZ`, as the exact rationals it gives.
    published = [
        [608311 / 1250200, 189793 / 714400, 198249 / 1000160],
        [35783 / 156275, 247089 / 357200, 198249 / 2500400],
        [0.0, 32229 / 714400, 5220557 / 5000800],
    ]
    for derived_row, published_row in zip(derived, published, strict=True):
        for got, want in zip(derived_row, published_row, strict=True):
            assert got == pytest.approx(want, abs=1e-12)


@pytest.mark.parametrize("matrix", [LINEAR_P3_TO_LINEAR_SRGB, XYZ_D65_TO_LINEAR_SRGB])
def test_each_conversion_matrix_sends_white_to_white(matrix):
    """display-p3, sRGB and XYZ here are all relative to D65, so white has to
    survive each matrix. A transcription slip in any coefficient shows up as a
    colour cast on greys, which is the hardest kind to notice by eye."""
    white = (
        (1.0, 1.0, 1.0)
        if matrix is LINEAR_P3_TO_LINEAR_SRGB
        else (
            0.9504559270516716,
            1.0,
            1.0890577507598784,
        )
    )
    for row in matrix:
        assert sum(
            coefficient * value for coefficient, value in zip(row, white, strict=True)
        ) == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize(
    "rgbf", [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.2, 0.5, 0.7), (1.0, 0.0, 0.0)]
)
def test_color_srgb_is_the_colour_it_names(rgbf):
    """`color(srgb ...)` is just normalised RGB, so it has to agree exactly
    with building the same colour from `rgbf`."""
    written = " ".join(str(value) for value in rgbf)
    for got, want in zip(Color(f"color(srgb {written})").rgbf, rgbf, strict=True):
        assert got == pytest.approx(want, abs=1e-12)


def test_color_srgb_takes_percentages_as_well_as_numbers():
    assert Color("color(srgb 100% 0% 0%)") == Color("color(srgb 1 0 0)")
    assert Color("color(srgb 50% 50% 50%)") == Color("color(srgb 0.5 0.5 0.5)")


@pytest.mark.parametrize(
    "text",
    [
        "color(display-p3 1 1 1)",
        "color(srgb 1 1 1)",
        "color(srgb-linear 1 1 1)",
        "color(xyz 0.9504559270516716 1 1.0890577507598784)",
        "color(xyz-d65 0.9504559270516716 1 1.0890577507598784)",
    ],
)
def test_white_is_white_in_every_space_that_is_read(text):
    """The end-to-end form of the matrix check above: every one of these
    spaces is D65, so each of these is white and not a near-white."""
    assert Color(text) == Color("white")


def test_a_display_p3_colour_inside_srgb_is_converted_rather_than_clipped():
    """P3 covers sRGB, so a modest P3 value has an exact sRGB answer. If the
    matrix were wrong this would still produce *a* colour, which is why the
    matrix is checked separately above."""
    inside = Color("color(display-p3 0.2 0.5 0.7)")
    assert inside.hex_l == "#0082b7"
    ## And it is genuinely a conversion: the same numbers read as sRGB differ.
    assert inside != Color("color(srgb 0.2 0.5 0.7)")


def test_a_display_p3_colour_outside_srgb_is_clipped_and_says_nothing():
    """The documented compromise. P3 red has no sRGB equivalent, so it lands
    on sRGB red -- the same rule as every other out-of-gamut input here."""
    assert Color("color(display-p3 1 0 0)") == Color("red")


def test_color_carries_an_alpha():
    assert Color("color(srgb 1 0 0 / 50%)").alpha == pytest.approx(0.5)
    assert Color("color(display-p3 0 0 1 / 0.25)").alpha == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("color(rec2020 1 0 0)", "cannot read 'rec2020' yet"),
        ("color(prophoto-rgb 1 0 0)", "cannot read 'prophoto-rgb' yet"),
        ("color(a98-rgb 1 0 0)", "cannot read 'a98-rgb' yet"),
        ("color(xyz-d50 1 1 1)", "cannot read 'xyz-d50' yet"),
        ("color(nonsense 1 0 0)", "is not a predefined color space"),
        ("color(srgb 1 0)", "takes 3 components"),
        ("color(srgb 1 0 0 0 0)", "takes 3 components"),
        ("color()", "takes a color space and three components"),
        ("color(srgb 1 0 0 / 2)", "Alpha must be between 0 and 1"),
    ],
)
def test_a_color_function_that_cannot_be_read_says_why(text, message):
    """The four spaces in the specification that are not read say so by name,
    rather than being reported as unknown -- they are real and this package
    has not got to them."""
    assert is_css(text)
    with pytest.raises(InvalidColorError, match=message):
        Color(text)


def test_color_is_recognised_as_a_css_function():
    assert is_css("color(srgb 1 0 0)")
    assert is_css("COLOR(SRGB 1 0 0)")
    assert "color" in CSS_FUNCTION_NAMES


def test_a_misspelled_color_function_suggests_it():
    """`color` is read here but is not in the component table, so the
    suggestion has to draw on the wider list or it would never offer it."""
    with pytest.raises(UnknownColorError, match="Did you mean") as raised:
        Color("colr(srgb 1 0 0)")
    assert "'color'" in str(raised.value)
