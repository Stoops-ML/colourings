# colourings
[![PyPI - Version](https://img.shields.io/pypi/v/colourings)](https://pypi.org/project/colourings/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/colourings)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/colourings?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BRIGHTGREEN&left_text=downloads)](https://pepy.tech/projects/colourings)
[![codecov](https://codecov.io/github/Stoops-ML/colourings/graph/badge.svg?token=NQUPC3NY6S)](https://codecov.io/github/Stoops-ML/colourings)

`colourings` is a lightweight Python library for creating, converting, comparing, and interpolating colors.

It provides:
- A high-level `Color` object with rich read/write properties.
- Function-based conversions when you want minimal overhead.
- Support for RGB/RGBA, HSL/HSLA, HEX, and named web colors.
- Deterministic color picking for arbitrary Python objects.

This project is a modernized fork of [vaab/colour](https://github.com/vaab/colour/) with additional formats, typing, revised channel ranges, and updated packaging.

## Migrating to 2.0

Two things changed that code may notice, and one that it cannot:

- **`Colour` is now `Color` itself**, not a subclass. `Colour is Color` is
  `True`, `type(Colour("red"))` is `Color`, and a `Colour` stays a `Colour`
  through a scale — which it did not before, since every constructor handed
  back a `Color`. Only code that told the two apart with `isinstance` or
  `type(...) is` is affected.
- **The named-color accessors are `NAMED_HSL`, `NAMED_RGB` and `NAMED_HEX`.**
  The old `HSL`, `RGB` and `HEX` still work and emit a `DeprecationWarning`
  naming the replacement. They were renamed because they shadowed the tuple
  types of the same name in `colourings.definitions`.
- **`pick_for` now picks the same color in every process.** Its default key
  ran hashable values through `hash()`, which Python salts per run, so those
  colors changed on every restart — nothing could have depended on them.
  Values that *were* stable, the unhashable ones, are unchanged. Pass
  `pick_key=hash_or_str` for the old behaviour.

## Installation

```bash
pip install colourings
```

## Quick Start

```python
from colourings import Color

blue = Color("blue")
print(blue)  # blue
print(blue.hex)  # #00f
print(blue.hex_l)  # #0000ff
print(blue.rgb)  # RGB(red=0.0, green=0.0, blue=255.0)
print(blue.hsl)  # HSL(hue=240.0, saturation=100.0, lightness=50.0)

blue.red = 255
print(blue.web)  # magenta
```

## Value Ranges

The library uses explicit numeric ranges (not mixed 0..1 + 0..255 conventions):

- `rgb`: channels in `[0, 255]`
- `rgba`: channels in `[0, 255]` (including alpha)
- `rgbf`: channels in `[0, 1]`
- `rgbaf`: channels in `[0, 1]`
- `hsl`: `(hue, saturation, lightness)` as `hue in [0, 360]`, `saturation/lightness in [0, 100]`
- `hsla`: same as `hsl`, with alpha in `[0, 100]`
- `hslf` / `hslaf`: channels in `[0, 1]`
- `hsv`: `(hue, saturation, value)` as `hue in [0, 360]`, `saturation/value in [0, 100]`
- `xyz`: CIE XYZ under D65, scaled so that white has `y` of 100
- `lab`: CIE L*a*b*, lightness in `[0, 100]`, a/b in `[-128, 127]`
- `lch`: cylindrical CIE L*a*b*, chroma in `[0, 182]`, hue in `[0, 360]`
- `oklab`: Oklab, lightness in `[0, 1]`, a/b in `[-0.4, 0.4]`
- `oklch`: cylindrical Oklab, chroma in `[0, 0.4]`, hue in `[0, 360]`
- `cmyk`: channels in `[0, 100]`
- `yuv`: BT.601, luma in `[0, 1]`, U in `[-0.436, 0.436]`, V in `[-0.615, 0.615]`
- `Color.alpha`: always `[0, 1]`

### Ranges Are Not the Gamut

Those ranges say what a format accepts, not what sRGB can show. `lab`, `lch`,
`oklab`, `oklch`, `xyz` and `yuv` can each name a color outside sRGB, and a
`Color` holds sRGB, so such a value is **clipped** on the way in — quietly, and
often: 88% of the `lab` triples in the range above do not survive.

```python
from colourings import Color

Color(lab=(100, 120, -120)).lab
# LAB(lightness=95.85895978712477, a=8.621537162382786, b=-6.079793114528798)
# -- not the color that went in
```

A clipped color is indistinguishable afterwards from one that was always in
gamut, because what it stores is the clipped value. So ask before building it:

```python
from colourings import Color, in_srgb_gamut

in_srgb_gamut((53.2408, 80.0925, 67.2032), "lab")  # True, this is red
in_srgb_gamut((100, 120, -120), "lab")  # False, this would be clipped
```

`tolerance` is measured in 8-bit levels and defaults to half a level, so the
default answers "would clipping change the color as rendered". Pass
`tolerance=0` to test the gamut exactly. The boundary is sharp, and every fully
saturated color sits exactly on it, so a primary written to few enough decimal
places really does fall outside and is reported as such.

Every other format — `rgb`, `hsl`, `hsv`, `cmyk`, `hex`, `web` and their
variants — is bounded by its own ranges, so it is representable by construction
and converts exactly. `in_srgb_gamut` raises `ValueError` if asked about one.

## Constructing Colors

All of these produce equivalent red colors:

```python
from colourings import Color

Color("red")
Color("#f00")
Color("#ff0000")
Color(hsl=(0, 100, 50))
Color(hsla=(0, 100, 50, 100))
Color(rgb=(255, 0, 0))
Color(rgba=(255, 0, 0, 255))
Color(rgbf=(1, 0, 0))
Color(rgbaf=(1, 0, 0, 1))
Color(hsv=(0, 100, 100))
Color(lab=(53.2408, 80.0925, 67.2032))
Color(lch=(53.2408, 104.5518, 40))
Color(oklab=(0.62796, 0.22486, 0.12585))
Color(oklch=(0.62796, 0.25768, 29.2339))
Color(xyz=(41.2456, 21.2673, 1.9334))
Color(cmyk=(0, 100, 100, 0))
Color(yuv=(0.299, -0.147108, 0.614777))
Color(Color("red"))
Color("rgb(255 0 0)")  # and the other CSS forms, below
Color("#ff000080")  # hex with alpha
```

Only one color input source is allowed per constructor call.

Copying a color carries its alpha across. An explicit `alpha` overrides the
copied one, rather than having to agree with it:

```python
translucent = Color(rgba=(255, 0, 0, 128))
Color(translucent).alpha  # 0.502
Color(translucent, alpha=0.25).alpha  # 0.25
```

A bare sequence is identified from its length and its component ranges, and a
four-component one keeps the alpha it carries:

```python
Color((255, 200, 200))  # RGB
Color((255, 200, 200, 128))  # RGBA, alpha 0.502
```

That only works where the ranges tell the formats apart. `(0, 0, 0)` is
equally valid RGB and HSL, so it raises `AmbiguousColorError`; name the format
to settle it.

Any remaining keyword sets a writable property once the color is built, which
is how you say "this color, but darker" in one call:

```python
Color("red", lightness=0).hsl  # HSL(hue=0.0, saturation=100.0, lightness=0.0)
```

Each goes through its own setter, so it is validated the same way an
assignment would be — `Color("red", lightness=200)` raises. This is not a way
to attach arbitrary attributes: `Color` defines `__slots__`, so an unknown name
raises `AttributeError` instead of quietly becoming one. A subclass that does
not redeclare `__slots__` has a `__dict__`, and does accept any name.

## Reading and Updating Channels

```python
from colourings import Color

c = Color("blue")

# Read
print(c.hue, c.saturation, c.lightness)
print(c.red, c.green, c.blue)
print(c.alpha)

# Update
c.hue = 0
c.saturation = 50
c.lightness = 75
c.alpha = 0.5

print(c.hsla)  # HSLA(hue=0.0, saturation=50.0, lightness=75.0, alpha=50.0)
print(c.rgbaf)  # RGBAf(red=0.875, green=0.625, blue=0.625, alpha=0.5)
```

## Gradients and Color Scales

### Between Two Colors

```python
from colourings import Color

red = Color("red")
blue = Color("blue")

print(list(red.range_to(blue, 5)))
# [<Color red>, <Color #ff007f>, <Color magenta>, <Color #7f00ff>, <Color blue>]

print(list(red.range_to(blue, 5, longer=True)))
# Takes the longer hue path around the color wheel.
# [<Color red>, <Color yellow>, <Color lime>, <Color cyan>, <Color blue>]
```

### Multi-Stop Scales

```python
from colourings import Color, color_scale

stops = (Color("black"), Color("orange"), Color("blue"), Color("white"))
palette = color_scale(stops, 10)

for color in palette:
    print(color)
# black #39221c #8e4d1c orange #ff003c #e100ff blue #bd71e3 #e3c6d9 white
```

`color_scale` requires at least two colors, and `num_steps >= len(colors)`.

### Interpolation Space

Both `color_scale` and `range_to` take a `space`, one of `hsl`, `lab`, `lch`,
`oklab` or `oklch`. It defaults to `hsl`, which is what these functions have
always used, but `hsl` is the weakest of the five for a gradient: it is polar,
so it swings through hues that are in neither endpoint, and its lightness is
not a perceptual quantity, so the steps come out unevenly spaced.

```python
from colourings import Color

red = Color("red")

print(list(red.range_to("cyan", 5)))
# HSL invents a magenta and a violet that are in neither endpoint.
# [<Color red>, <Color #ff00bf>, <Color #7f00ff>, <Color #0040ff>, <Color cyan>]

print(list(red.range_to("cyan", 5, space="oklab")))
# Oklab blends the two, in evenly sized perceptual steps.
# [<Color red>, <Color #ee745b>, <Color #d2a993>, <Color #a3d6c9>, <Color cyan>]
```

Reach for `oklab`. It is perceptually uniform, so its steps are evenly spaced,
and rectangular, so there is no hue arc to sweep. Use `oklch` when that sweep
is the point, and `lab` or `lch` for the CIE equivalents.

`longer` chooses the arc around the hue circle, so it applies only to a space
that has a hue: passing it with `oklab` or `lab` raises `ValueError`.

A straight line between two saturated colors can leave the sRGB gamut. Those
points are clamped, as everywhere else in the library, so a scale through one
of them is a shade off the exact interpolant.

### Alpha

Alpha is interpolated alongside the color, so a scale can fade as well as
shift. It belongs to no color space, so `space` does not apply to it and it is
always interpolated linearly:

```python
from colourings import Color

opaque = Color("red", alpha=1.0)
clear = Color("blue", alpha=0.0)
print([c.alpha for c in opaque.range_to(clear, 5)])  # [1.0, 0.75, 0.5, 0.25, 0.0]
```

A scale between colors that are all opaque is unaffected. The endpoints keep
their alpha exactly, so a scale ending on a color reproduces it.

## Equality Behavior

By default, `Color` equality compares RGB-equivalent rendered color (`hex_l`).

```python
from colourings.colour import Color

assert Color("red") == Color("#f00")
```

You can plug in a custom comparison function:

```python
from colourings.colour import Color, HSL_equivalence

c1 = Color("red", lightness=0, equality=HSL_equivalence)
c2 = Color("blue", lightness=0, equality=HSL_equivalence)

print(c1 == c2)  # False
```

The strategy is a comparison policy rather than part of the color, so
`Color(other)` does not inherit it — it copies the value and starts from the
default. `copy.copy` duplicates both:

```python
import copy

from colourings.colour import Color, HSL_equivalence, RGB_equivalence

c = Color("red", equality=HSL_equivalence)
print(Color(c).equality is RGB_equivalence)  # True, the default
print(copy.copy(c).equality is HSL_equivalence)  # True
```

### What `==` costs, and `equals`

`==` consults both operands and accepts either verdict, which keeps it
symmetric but has three consequences. None of them bite while every color uses
the default:

- **It is not transitive across mixed strategies.** With `a` and `c` strict and
  `b` loose, `a == b` and `b == c` can both hold while `a == c` does not —
  and `set`, `dict`, `in` and `assertEqual` all assume otherwise.
- **A strict strategy only holds where both colors carry it**, since the looser
  one need only agree once to satisfy the `or`.
- **A strategy looser than `hex_l` breaks the hash contract**, so `b in {a}` can
  be `False` where `a == b`. A *stricter* one is fine: `HSL_equivalence` lets
  two colors share a hash while comparing unequal, which is an ordinary
  collision that `set` resolves by comparing.

`equals` has none of these. It takes the strategy as an argument rather than
from the operands, so it is reflexive, symmetric and transitive whenever that
strategy is — and both built-ins are:

```python
from colourings import Color, HSL_equivalence

Color("red").equals("#f00")  # True, by hex_l
Color("red").equals("#f00", HSL_equivalence)  # True, by HSL
```

Use `equals` where the answer matters and `==` where the default is fine.

## Deterministic Color Picking for Objects

Use `pick_for` to map Python objects to colors:

```python
from colourings.colour import Color

print(Color(pick_for="user:123") == Color(pick_for="user:123"))  # True
print(Color(pick_for="user:123") == Color(pick_for="user:456"))  # False
```

The same value gives the same color in every process, so a color picked for a
user, a host or a branch survives a restart:

```python
print(Color(pick_for="user:123").hex_l)  # #1b1069, every run
```

The one exception is an object relying on the default `__repr__`, whose string
form contains its address — that changes every run and between instances, and
no key function can recover from it. Give such a class a `__str__`, or pass a
`pick_key` that reads the fields you care about.

You can override the picking strategy with:
- `picker`: callable that returns a color-like value
- `pick_key`: callable that maps objects to comparable keys

`hash_or_str` was the default and is still available for keys that should hold
within one process and be discarded with it. It runs hashable objects through
`hash()`, which Python salts per process — and because the key it builds
contains the type name, and string hashing is what gets salted, *every*
hashable object came out a different color each run while every unhashable one
was stable. Which of those you got depended on nothing you would think to care
about, so it is no longer the default.

## Convenience Objects and Aliases

```python
from colourings.colour import NAMED_HEX, NAMED_HSL, NAMED_RGB
from colourings import Colour

print(NAMED_HSL.BLUE)  # HSL(hue=240.0, saturation=100.0, lightness=50.0)
print(NAMED_RGB.BLUE)  # RGB(red=0.0, green=0.0, blue=255.0)
print(NAMED_HEX.BLUE)  # #00f

assert Colour("red") == Colour("#f00")
```

`Colour` is `Color` — the same class under the British spelling, not a subclass
of it, so `Colour is Color` and a `Colour` stays one through a scale.

## CSS Syntax

Colors can be read from, and written back to, the syntax CSS uses:

```python
from colourings import Color

Color("rgb(255, 0, 0)")  # legacy commas
Color("rgb(255 0 0 / 50%)")  # CSS Color 4, alpha after a slash
Color("hsl(0deg 100% 50%)")  # deg, grad, rad and turn all work
Color("oklch(0.62796 0.25768 29.23389)")
Color("#ff000080")  # an 8-digit hex, and #RGBA
Color("transparent")  # black with no alpha
```

`rgb`, `rgba`, `hsl`, `hsla`, `lab`, `lch`, `oklab` and `oklch` are read, with
either comma or space separators, in any case, and with surrounding whitespace
ignored. Whitespace is now ignored around every string form, not just these.

```python
Color("red").to_css()  # '#f00'
Color("red", alpha=0.5).to_css("rgb")  # 'rgb(255 0 0 / 0.5)'
Color("red").to_css("hsl")  # 'hsl(0 100% 50%)'
Color("red").to_css("oklch")  # 'oklch(0.62796 0.25768 29.23389)'
```

Output uses the space-separated syntax a browser itself serialises to, and
includes the alpha only when the color is not opaque. Every form round-trips
exactly: reading back what `to_css` wrote gives the same 8-bit color, alpha
included.

Three things to know:

- **Out of range is an error, not a clamp.** A browser reads `rgb(300 0 0)` as
  red; here it raises. Quietly turning one color into another is what this
  library avoids elsewhere, and reading a stylesheet is not a reason to start.
- **Percentages scale against a different reference in each function**, which
  is what CSS Color 4 specifies rather than anything this library chose:

  | function | axis | `100%` |
  | --- | --- | --- |
  | `rgb()` | `r`, `g`, `b` | 255 |
  | `hsl()` | `s`, `l` | 100 |
  | `lab()`, `lch()` | `L` | 100 |
  | `lab()` | `a`, `b` | ±125 |
  | `lch()` | `C` | 150 |
  | `oklab()`, `oklch()` | `L` | 1 |
  | `oklab()` | `a`, `b` | ±0.4 |
  | `oklch()` | `C` | 0.4 |

  So `oklch(0.5 50% 200)` is exactly `oklch(0.5 0.2 200)`. `100%` is the
  reference and not a maximum: a larger percentage is allowed by the syntax
  and then refused by the range check, exactly as the equivalent number is.

- **System colors are recognised and deliberately not resolved.** `Canvas`,
  `ButtonFace`, `LinkText` and the rest are defined by CSS as whatever the
  reader's platform, browser and theme make them, so any fixed value would be
  wrong for most readers and right for nobody. `Color("Canvas")` raises
  `UnknownColorError`, saying that it *is* a system color and that there is no
  fixed color to return, rather than reporting it as an unidentifiable typo.
  The deprecated ones from the specification's appendix — `ThreeDShadow`,
  `InfoBackground` and the rest — are recognised the same way.

## Adjusting a Color

Every one of these returns a new color and leaves the original alone, carrying
its alpha across:

```python
from colourings import Color

c = Color("#3d7ab8")

c.lighten(0.2)  # and darken, saturate, desaturate
c.rotate_hue(180)
c.grayscale()  # the same method as greyscale()
c.invert()
c.mix("white", 0.3)
```

### Absolute and relative steps

`lighten`, `darken`, `saturate` and `desaturate` take an amount in `[0, 1]` and
a `relative` flag that decides how to read it:

- **relative** (the default) — a fraction of the distance still available. A
  step can never clip, and `1.0` lands exactly on the limit, so
  `lighten(1.0)` is white and `darken(1.0)` is black.
- **absolute** (`relative=False`) — a fraction of the whole range, added flat
  and clamped. This is what Sass's `lighten()` does.

```python
Color("#e0e0e0").lightness  # 87.84
Color("#e0e0e0").lighten(0.1).lightness  # 89.06, a tenth of what was left
Color("#e0e0e0").lighten(0.1, relative=False).lightness  # 97.84, a flat +10
```

These move HSL lightness and saturation, which are geometric rather than
perceptual quantities. For a step that looks the same size wherever it starts,
`mix` toward white or black in `oklab` instead.

### `grayscale` is not `desaturate(1.0)`

They produce different greys, and the difference is large:

```python
Color("blue").desaturate(1.0)  # <Color #7f7f7f> -- holds HSL lightness
Color("blue").grayscale()  # <Color #4c4c4c> -- holds luminance
Color("yellow").grayscale()  # <Color #f7f7f7>
```

Desaturating holds HSL lightness, so every fully saturated color collapses to
the same mid grey whatever its brightness. `grayscale` holds relative luminance
exactly, so blue stays dark and yellow stays bright — which is what you want
when the grey has to stand in for the color.

### Mixing

```python
Color("red").mix("blue")  # <Color #8c53a2>, halfway in oklab
Color("red").mix("blue", 0.25)  # <Color #c6496d>
Color("red").mix("blue", 0.5, space="hsl")  # <Color magenta>
```

`mix` defaults to `oklab`, unlike `color_scale`, which defaults to `hsl` only
because changing it would move every existing caller's output. Alpha is blended
too, so mixing an opaque color with a transparent one fades.

## Contrast and Luminance

`Color.relative_luminance` is WCAG 2.x relative luminance, and
`Color.contrast_ratio` is the ratio built from it:

```python
from colourings import Color

Color("black").contrast_ratio("white")  # 21.0
Color("#767676").contrast_ratio("white")  # 4.5422...
Color("white").relative_luminance  # 1.0
Color("red").relative_luminance  # 0.2126
```

`contrast_ratio` takes any supported input format, and is symmetric — which
color is the text and which the background does not matter.

`is_readable` applies the WCAG thresholds, and `best_text_color` picks whichever
candidate contrasts most:

```python
Color("#767676").is_readable("white")  # True, 4.54 clears AA
Color("#777777").is_readable("white")  # False, 4.48 does not
Color("#777777").is_readable("white", size="large")  # True, large text needs 3
Color("#777777").is_readable("white", level="AAA")  # False, AAA needs 7

Color("navy").best_text_color()  # <Color white>
Color("navy").best_text_color(["#eeeeee", "#333333"])  # <Color #eee>
```

| level | size | minimum |
| --- | --- | --- |
| `AA` | `normal` | 4.5 |
| `AA` | `large` | 3 |
| `AAA` | `normal` | 7 |
| `AAA` | `large` | 4.5 |

Large means 18pt, or 14pt bold. The table is
`colourings.definitions.WCAG_CONTRAST_MINIMUMS`. `is_readable` compares against
the exact ratio rather than a rounded one, so a pair at 4.4999 fails `AA` even
though it would display as "4.50" — which is where it can disagree with a tool
that rounds first. `best_text_color` judges on contrast alone, and a tie goes to
whichever candidate came first, so their order is worth choosing.

Alpha plays no part on either side. A contrast ratio is between two opaque
colors, and a translucent one has no contrast of its own: it depends on
whatever shows through it. Composite first, then ask.

> **`Color.luminance` is a different quantity, and is not the one to use here.**
> It is the root mean square of the channels under BT.601's luma weights, taken
> without linearising them — a rough model of how bright a color *looks*, not of
> how much light it carries. `#777777` is `0.467` by `luminance` and `0.185` by
> `relative_luminance`. It keeps its name and behaviour because that is what it
> has always returned.

The pure-function forms are `rgb2relative_luminance` and `contrast_ratio`, both
in `colourings.conversions`.

## Named Components

Conversions and the `Color` tuple attributes return named tuples, so components
can be read by name:

```python
from colourings import Color
from colourings.definitions import RGB

c = Color("red")

print(c.rgb.red)  # 255.0
print(c.hsl.hue)  # 0.0
print(c.rgbaf.alpha)  # 1.0
```

They are still ordinary tuples, so comparing, unpacking, indexing and hashing
against plain tuples behave exactly as before, and assignment still accepts any
sequence:

```python
r, g, b = c.rgb
assert c.hsl == (0.0, 100.0, 50.0)
assert isinstance(c.rgb, RGB)

c.rgb = (0.0, 0.0, 255.0)
```

The types are `RGB`, `RGBA`, `HSL`, `HSLA` and their normalised `RGBf`, `RGBAf`,
`HSLf` and `HSLAf` counterparts, all importable from `colourings.definitions`.
They used to share their names with the accessor objects in
`colourings.colour`, which is why those are now `NAMED_HSL`, `NAMED_RGB` and
`NAMED_HEX`.

## Function-Based Conversions

Use direct conversion helpers when you do not need the class API:

```python
from colourings.conversions import rgb2hex, rgb2hsl, web2rgb, hsl2web

print(rgb2hex((255, 0, 0)))  # #f00
print(rgb2hsl((255, 0, 0)))  # HSL(hue=0.0, saturation=100.0, lightness=50.0)
print(web2rgb("rebeccapurple"))  # RGB(red=102.0, green=51.0, blue=153.0)
print(hsl2web((0, 0, 50.2)))  # gray
```

Available helpers include conversion paths across:
- `rgb`, `rgba`, `rgbf`, `rgbaf`
- `hsl`, `hsla`, `hslf`, `hslaf`
- `hsv`
- `xyz`, `lab`, `lch` (CIE, D65)
- `oklab`, `oklch`
- `cmyk`, `yuv`
- `hex` and `web`

Conversions are memoized with a bounded LRU cache, so repeated lookups of the
same color are served from the cache. Results are immutable, so callers may
share them safely, and repeated calls return the identical object:

```python
from colourings.conversions import clear_caches, rgb2hsl

assert rgb2hsl((255, 0, 0)) is rgb2hsl((255, 0, 0))

# Releases the cached results. Never needed for correctness.
clear_caches()
```

Comparing against anything that is not a color is `False` rather than an error,
and colors are hashable, so they work in sets and as dict keys:

```python
assert Color("red") != "red"
assert len({Color("red"), Color("#f00"), Color("blue")}) == 2
assert {Color("red"): "warm"}[Color("#f00")] == "warm"
```

`==` consults both operands' strategies, so it is symmetric even when the two
colors carry different ones. The hash follows `hex_l`, which matches both
built-in strategies; a custom `equality` that treats colors with different
`hex_l` as equal breaks that correspondence, and those colors should not be
used as dict keys. `Color` is mutable, so do not mutate one while it is held
in a set.

## Perceptual Spaces

`lab`, `lch`, `oklab` and `oklch` are perceptually uniform, so they are the
ones to interpolate or measure distance in. `lch` and `oklch` are the polar
forms, which makes them the convenient ones for adjusting lightness or chroma
without shifting hue.

```python
from colourings import Color

c = Color("rebeccapurple")
print(c.lab)  # LAB(lightness=32.9024..., a=42.8830..., b=-47.1486...)
print(c.lch)  # LCH(lightness=32.9024..., chroma=63.7334..., hue=312.2874...)
print(c.oklab)  # OKLAB(lightness=0.4402..., a=0.0881..., b=-0.1338...)
print(c.oklch)  # OKLCH(lightness=0.4402..., chroma=0.1602..., hue=303.3729...)

lighter = Color(lch=(c.lch.lightness + 20, c.lch.chroma, c.lch.hue))
```

`oklab` is the more uniform of the two pairs, most visibly around blue, where
CIE L*a*b* is known to bend. It is also on a different scale: lightness runs
`[0, 1]` rather than `[0, 100]`, and its chroma axes `[-0.4, 0.4]` rather than
`[-128, 127]`, matching the CSS `oklab()` and `oklch()` functions.

The CIE conversions use the D65 illuminant, which is the one sRGB is defined
against. Values are not interchangeable with a library that uses D50. Oklab is
defined against D65 too, but is derived from sRGB directly rather than through
this library's XYZ, whose seven-digit matrix is not precise enough to leave a
grey neutral in Oklab. Converting into sRGB clamps anything outside its gamut,
since an out-of-gamut colour has no sRGB encoding; see
[Ranges Are Not the Gamut](#ranges-are-not-the-gamut) for how to check first.

## Colour Difference

How far apart two colors are, and what to call one:

```python
from colourings import Color

Color("black").delta_e("white")  # 100.0
Color("#ff0000").delta_e("#ff0001")  # 0.098..., invisible
Color("#123456").nearest_name()  # 'midnightblue'
```

Four metrics, in the order they were standardised:

| metric | what it is |
| --- | --- |
| `cie76` | Euclidean distance in CIE L\*a\*b\*. Fast, and overstates blues badly |
| `cie94` | Weights lightness, chroma and hue separately. Not symmetric — see below |
| `ciede2000` | What "delta E" means unqualified. The default |
| `ok` | Euclidean distance in Oklab. Perceptual and cheap, on its own scale |

Roughly, on the three L\*a\*b\* metrics: 1 is the smallest difference a good eye
can see side by side, 2 to 3 is noticeable, above 5 they read as different
colors. `ok` numbers are much smaller — Oklab's axes run to about 0.4, not 100
— so a threshold does not carry across.

The blue case is worth seeing, since it is why the later metrics exist:

```python
from colourings.difference import delta_e_cie76, delta_e_ciede2000

blue1, blue2 = (32.0, 79.0, -104.0), (32.0, 69.0, -100.0)
delta_e_cie76(blue1, blue2)  # 10.77
delta_e_ciede2000(blue1, blue2)  # 2.77
```

> **On `cie94`:** it is asymmetric by construction, and by a lot rather than a
> little. The chroma and hue terms are divided by weights that grow with the
> *first* argument's chroma, so a dull reference down-weights nothing and
> reports the larger distance:
>
> ```python
> grey, magenta = Color("#808080"), Color("#ff00ff")
> grey.delta_e(magenta, metric="cie94")     # 115.7
> magenta.delta_e(grey, metric="cie94")     # 19.8
> ```
>
> Pass the two in the order you mean, or use `ciede2000`, which exists partly
> because of this.

`nearest_name` searches all 152 named colors and defaults to `ok`, being the
cheap perceptual one. It returns the lowercase name; `web` gives the canonical
spelling for an exact match. It always returns *something*, however far away —
check `delta_e` against it before quoting it.

> **On `ciede2000`:** its constants were written from the formula rather than
> copied from a reference implementation, so they are checked against the
> published Sharma–Wu–Dalal supplementary test data — all 34 pairs, to the four
> decimals that table gives.
>
> That check is worth more than it sounds. The properties this function is
> otherwise tested against — exactly 0 against itself, exactly 100 for black
> against white, symmetry, and the neutral lightness reduction — all still pass
> with the hue-rotation peak moved from 275° to 257°, or with a weighting
> constant mistyped. The published pairs catch every one of those.

## Compositing

`over` draws this color on another, which is what its alpha means:

```python
from colourings import Color

Color("red", alpha=0.5).over("white").rgb
# RGB(red=255.0, green=127.5, blue=127.5)
```

`blend` does the same through any of CSS's sixteen blend modes.

Twelve are **separable** — each channel is blended on its own:
`normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`, `color-dodge`,
`color-burn`, `hard-light`, `soft-light`, `difference`, `exclusion`.

```python
Color("red").blend("cyan", "multiply")  # <Color black>
Color("red").blend("cyan", "screen")  # <Color white>
Color("black").blend("#3d7ab8", "color-dodge")  # <Color #3d7ab8>, unchanged
```

Four are **non-separable**: they read all three channels together, taking some
of hue, saturation and luma from each operand.

| mode | takes from the source | takes from the backdrop |
| --- | --- | --- |
| `hue` | hue | saturation and luma |
| `saturation` | saturation | hue and luma |
| `color` | hue and saturation | luma |
| `luminosity` | luma | hue and saturation |

```python
# Tint a grey with a colour's hue, keeping the grey's lightness.
Color("#3d7ab8").blend("#808080", "color")  # <Color #4e8bc9>

# luminosity is color with the operands swapped, exactly.
Color("red").blend("cyan", "luminosity") == Color("cyan").blend("red", "color")
# True
```

Their *luma* is the spec's `Lum` — `0.3R + 0.59G + 0.11B` on the channels as
they stand — and **not** the WCAG relative luminance that
[`luminance`](#contrast-and-luminance) reports, which uses different
coefficients on linearised channels. The two are not interchangeable, and only
one of them is what a browser blends with.

This color is the source and the argument is the backdrop, the same way round
as CSS, so the result is what a browser shows for an element of this color over
that background. The result's alpha is `a + b * (1 - a)`, so an opaque backdrop
gives an opaque result.

### Encoded or linear

Compositing happens on the channels **as encoded**, which is what CSS, canvas
and every renderer do — and is not the physically correct answer, because light
adds linearly and sRGB is not linear in light. The gap is not subtle:

```python
Color("red", alpha=0.5).over("white").green  # 127.5, what a browser shows
Color("red", alpha=0.5).over("white", linear=True).green  # 187.516...
```

Sixty channel steps. Encoded is the default because it is what you are
comparing against; pass `linear=True` when you want the physical answer, and
expect no browser to agree with it.

The non-separable modes — `hue`, `saturation`, `color`, `luminosity` — are not
implemented, and `blend` raises rather than quietly doing something else.

## Harmonies

Hue relationships, as new colors carrying this one's alpha:

```python
from colourings import Color

Color("red").complementary()  # <Color cyan>
Color("red").triadic()  # (<Color red>, <Color lime>, <Color blue>)
Color("red").tetradic()
# (<Color red>, <Color chartreuse>, <Color cyan>, <Color #7f00ff>)
Color("red").analogous()  # (<Color #ff007f>, <Color red>, <Color #ff7f00>)
Color("red").analogous(60)  # (<Color magenta>, <Color red>, <Color yellow>)
```

The base color is included, and `analogous` puts it in the middle, so each
result reads in wheel order.

## Light or Dark

```python
Color("navy").is_dark  # True
Color("yellow").is_light  # True
```

The threshold is not a matter of taste: it is the luminance at which contrast
against white equals contrast against black, so `is_dark` is exactly "white
text reads better on this than black" and never disagrees with
`best_text_color`.

## Previewing a Color

In a notebook, a `Color` displays as a swatch — no toolkit, nothing to close:

```python
from colourings import Color

# Each of these renders as a colored square with its name. A translucent
# one is drawn over a checkerboard, so its alpha is visible.
Color("rebeccapurple")
Color("red", alpha=0.5)
```



`Color.preview()` opens a window filled with the color, sized in pixels.

```python
from colourings import Color

# The size is in pixels, and defaults to 200x200.
Color("rebeccapurple").preview()
Color("rebeccapurple").preview(400, 100)
```

An alpha other than `1` is not rendered, and warns.

This is the only part of the library that needs a GUI toolkit. `tkinter` is
imported inside the method rather than at module scope, so `import colourings`
neither pays for it -- tkinter costs roughly three times what the rest of this
package does to import, since it loads a C extension and links Tcl/Tk -- nor
fails on a machine that does not have it.

Being in the standard library does not mean it is installed. CPython ships
`tkinter` on Windows and macOS, but most Linux distributions package it
separately, and a minimal install or a slim container image will not have it.
Calling `preview()` there raises `ImportError` naming what to install:
`python3-tkinter` on the Red Hat family, `python3-tk` on Debian and Ubuntu.
Every other part of the library works without it.

## Error Handling

Every failure caused by a value that is not a usable color derives from
`ColorError`, so one `except` covers them all:

```python
from colourings import Color, ColorError

user_input = "chartruese"  # a misspelling of chartreuse

try:
    Color(user_input)
except ColorError as e:
    print(f"not a color: {e}")
# not a color: Cannot identify color 'chartruese'. Did you mean 'chartreuse'?
```

That suggestion is not only for names. A string that is nearly a color gets
told what it is nearly:

| typed | said |
| --- | --- |
| `rde` | `Did you mean 'red'?` |
| `gren` | `Did you mean 'green', 'grey' or 'seagreen'?` |
| `rbg(1 2 3)` | `There is no color function called 'rbg'. Did you mean 'rgb'?` |
| `#ff000` | `A hexadecimal color takes 3, 4, 6 or 8 digits, and this has 5.` |
| `xyzzy` | nothing beyond `Cannot identify color 'xyzzy'.` |

Nothing is offered unless it is close, since a suggestion for everything would
make the ones worth reading harder to trust. At most three are given.

The subclasses say what went wrong:

| Exception | Raised when |
| --- | --- |
| `InvalidColorError` | A value is not valid in the format it was given as |
| `AmbiguousColorError` | A value reads as more than one format, e.g. `Color((0, 0, 0))` |
| `UnknownColorError` | A value matches no supported format, e.g. `Color("nope")` |

`ColorError` derives from both `ValueError` and `TypeError`, so existing
`except ValueError` and `except TypeError` clauses keep working unchanged.

Errors about how a helper was *called* -- more than one color argument to
`Color`, a scale with fewer than two colors -- stay plain `ValueError` or
`TypeError`, since they are not about a color value.

## API Surface

Top-level exports:

```python
from colourings import (
    AmbiguousColorError,
    Color,
    ColorError,
    Colour,
    HSL_equivalence,
    InvalidColorError,
    RGB_color_picker,
    RGB_equivalence,
    UnknownColorError,
    clear_caches,
    color_scale,
    colour_scale,
    identify_color,
    in_srgb_gamut,
    make_color_factory,
)
```

The conversion functions, the shape predicates and the CSS parser stay in their
own modules: they are a much larger surface than most callers want, and
importing the package should not put eighty names within reach of a typo.

- `colourings.colour`: the named-color accessors `NAMED_HSL`, `NAMED_RGB`, `NAMED_HEX`
- `colourings.conversions`: conversion utilities, plus `rgb2relative_luminance`, `contrast_ratio`, `in_srgb_gamut` and `clear_caches`
- `colourings.css`: `css2hsl`, `css2hsla`, `hsla2css`, `is_css`
- `colourings.difference`: `delta_e_cie76`, `delta_e_cie94`, `delta_e_ciede2000`, `delta_e_ok`, `hsl_difference`, `nearest_named_hsl`
- `colourings.identify`: type/shape predicates like `is_rgb`, `is_hsl`, `is_web`

## Contributing

Bug reports, colour-science corrections and pull requests are welcome.
[CONTRIBUTING.md](CONTRIBUTING.md) describes the checks CI runs, all of which
you can run locally, and what a change needs before it can be merged.

One rule is worth repeating here, because it is what most of this package is:
a wrong constant in colour arithmetic produces plausible output rather than an
error. Anything with published constants needs a citable source, and features
whose constants could not be confirmed raise rather than guessing.

## Security

To report a vulnerability, use
[GitHub's private reporting](https://github.com/Stoops-ML/colourings/security/advisories/new)
rather than a public issue. [SECURITY.md](SECURITY.md) sets out what is in
scope — the short version is that `colourings` performs no I/O, opens no
network connections and has no runtime dependencies, which leaves crafted
inputs and the release process itself.
