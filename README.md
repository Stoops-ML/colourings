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
```

Only one color input source is allowed per constructor call.

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
# black #39221c #8e4d1c orange #ff003c #e100ff blue #bd71e3 #e3c6d9
white
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

## Deterministic Color Picking for Objects

Use `pick_for` to map Python objects to stable colors:

```python
from colourings.colour import Color

print(Color(pick_for="user:123").web)  # #010000
print(Color(pick_for="user:123") == Color(pick_for="user:123"))  # True
```

You can override the picking strategy with:
- `picker`: callable that returns a color-like value
- `pick_key`: callable that maps objects to comparable keys

## Convenience Objects and Aliases

```python
from colourings.colour import HEX, HSL, RGB, Colour

print(HSL.BLUE)  # HSL(hue=240.0, saturation=100.0, lightness=50.0)
print(RGB.BLUE)  # RGB(red=0.0, green=0.0, blue=255.0)
print(HEX.BLUE)  # #00f

assert Colour("red") == Colour("#f00")
```

`Colour` is an alias subclass of `Color` for British spelling preference.

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
Note these are distinct from the same-named `colourings.colour.HSL` and
`colourings.colour.RGB` accessor objects that look up colors by name.

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

clear_caches()  # release cached results; never needed for correctness
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
since an out-of-gamut colour has no sRGB encoding.

## Previewing a Color

`Color.preview()` opens a window filled with the color, sized in pixels.

```python
from colourings import Color

Color("rebeccapurple").preview()  # 200x200 by default
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

try:
    Color(user_input)
except ColorError as e:
    print(f"not a color: {e}")
```

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
from colourings import Color, Colour, color_scale, colour_scale
from colourings import (
    ColorError,
    InvalidColorError,
    AmbiguousColorError,
    UnknownColorError,
)
```

Additional APIs are available from submodules:

- `colourings.colour`: `HSL_equivalence`, `RGB_equivalence`, `RGB_color_picker`, `make_color_factory`, `identify_color`, `HSL`, `RGB`, `HEX`
- `colourings.conversions`: conversion utilities and `clear_caches`
- `colourings.identify`: type/shape predicates like `is_rgb`, `is_hsl`, `is_web`
