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
- `hex` and `web`

## API Surface

Top-level exports:

```python
from colourings import Color, Colour, color_scale, colour_scale
```

Additional APIs are available from submodules:

- `colourings.colour`: `HSL_equivalence`, `RGB_equivalence`, `RGB_color_picker`, `make_color_factory`, `identify_color`, `HSL`, `RGB`, `HEX`
- `colourings.conversions`: conversion utilities
- `colourings.identify`: type/shape predicates like `is_rgb`, `is_hsl`, `is_web`
