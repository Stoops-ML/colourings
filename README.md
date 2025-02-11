# colourings
[![PyPI - Version](https://img.shields.io/pypi/v/colourings)](https://pypi.org/project/colourings/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/colourings)
[![codecov](https://codecov.io/github/Stoops-ML/colourings/graph/badge.svg?token=NQUPC3NY6S)](https://codecov.io/github/Stoops-ML/colourings)

Converts and manipulates common color representation (RGB, HSL, web, ...)

This is a fork of the [Colour](https://github.com/vaab/colour/) Python package. This fork contains a few changes:
- Support for RGBA and HSLA [#42](https://github.com/vaab/colour/issues/42)
- Add Teal [#58](https://github.com/vaab/colour/issues/58) and RebeccaPurple colors [#25](https://github.com/vaab/colour/pull/25)
- Correct luminance and lightness definitions [#64](https://github.com/vaab/colour/issues/64)
- Add `Colour` class [#46](https://github.com/vaab/colour/pull/46)
- Add `Color.preview` method [#63](https://github.com/vaab/colour/pull/63)
- Color scale uses shortest path [#50](https://github.com/vaab/colour/pull/50)
- `color_scale` can interpolate between more than two colors
- RGB values are between 0 and 255 and hue is between 0 and 360. This is in contrast to RGBA and HSLA values that are between 0 and 1
- Dedicated tests directory
- Add (limited) typing (not currently passing mypy)
- Updated project structure

Below is a modified copy of the readme from [Colour](https://github.com/vaab/colour/).

## Features

- Damn simple and pythonic way to manipulate color representation (see examples below)
- Full conversion between RGB, HSL, 6-digit hex, 3-digit hex, human color
- One object (`Color`) or bunch of single purpose function (`rgb2hex`, `hsl2rgb` ...)
- `web` format that use the smallest representation between 6-digit (e.g. `#fa3b2c`), 3-digit (e.g. `#fbb`), fully spelled color (e.g. `white`), following W3C color naming for compatible CSS or HTML color specifications.
- Smooth intuitive color scale generation choosing N color gradients.
- Can pick colors for you to identify objects of your application.

## Installation

```
pip install colourings
```

## Usage

To get complete demo of each function, please read the source code which is heavily documented and provide a lot of examples in doctest format.

Here is a reduced sample of a common usage scenario:

### Instantiation

Let's create blue color:

```
>>> from colourings import Color
>>> c = Color("blue")
>>> c
<Color blue>
```

Please note that all of these are equivalent examples to create the red color:

```
Color("red")               ## human, web compatible representation
Color("blue", hue=0)       ## hue of blue is 0.66, hue of red is 0.0
Color("#f00")              ## standard 3 hex digit web compatible representation
Color("#ff0000")           ## standard 6 hex digit web compatible representation
Color(hsl=(0, 1, 0.5))     ## full 3-uple HSL specification
Color(hsla=(0, 1, 0.5, 1)) ## full 4-uple HSLA specification
Color(rgb=(255, 0, 0))     ## full 3-uple RGB specification
Color(rgba=(1, 0, 0, 1))   ## full 4-uple RGBA specification
Color(Color("red"))        ## recursion doesn't break object
```

### Reading Values

Several representations are accessible:

```
>>> c.hex
'#00f'
>>> c.hsl
(0.66..., 1.0, 0.5)
>>> c.rgb
(0.0, 0.0, 1.0)
```

And their different parts are also independently accessible, as the different amount of red, blue, green, in the RGB format:

```
>>> c.red
0.0
>>> c.blue
1.0
>>> c.green
0.0
```

Or the hue, saturation and lightness of the HSL representation:

```
>>> c.hue
0.66...
>>> c.saturation
1.0
>>> c.lightness
0.5
```

A note on the `.hex` property, it'll return the smallest valid value when possible. If you are only interested by the long value, use `.hex_l`:

```
>>> c.hex_l
'#0000ff'
```

### Modifying Color Objects

All of these properties are read/write, so let's add some red to this color:

```
>>> c.red = 1
>>> c
<Color magenta>
```

We might want to de-saturate this color:

```
>>> c.saturation = 0.5
>>> c
<Color #bf40bf>
```

And of course, the string conversion will give the web representation which is human, or 3-digit, or 6-digit hex representation depending which is usable:

```
>>> f"{c}"
'#bf40bf'

>>> c.lightness = 1
>>> f"{c}"
'white'
```

### Ranges of Colors

You can get some color scale of variation between two `Color` objects quite easily. Here, is the color scale of the rainbow between red and blue:

```
>>> red = Color("red")
>>> blue = Color("blue")
>>> list(red.range_to(blue, 3))
[<Color red>, <Color magenta>, <Color blue>]
>>> list(red.range_to(blue, 5, longer=True))
[<Color red>, <Color yellow>, <Color lime>, <Color cyan>, <Color blue>]
```

Or the different amount of gray between black and white:

```
>>> black = Color("black")
>>> white = Color("white")
>>> list(black.range_to(white, 6))
[<Color black>, <Color #333>, <Color #666>, <Color #999>, <Color #ccc>, <Color white>]
```

If you have to create graphical representation with color scale between red and green ('lime' color is full green):

```
>>> lime = Color("lime")
>>> list(red.range_to(lime, 5))
[<Color red>, <Color #ff7f00>, <Color yellow>, <Color chartreuse>, <Color lime>]
```

Notice how naturally, the yellow is displayed in human format and in the middle of the scale. And that the quite unusual (but compatible) 'chartreuse' color specification has been used in place of the hexadecimal representation.

You can create your own scale with as many colors as you like:
```
>>> from colourings import color_scale
>>> color_scale((Color("black"), Color("orange"), Color("blue"), Color("white")), 10)
[Color("black"), Color("#39221c"), Color("#8e4d1c"), Color("orange"), Color("#ff003c"), Color("#e100ff"), Color("blue"), Color("#bd71e3"), Color("#e3c6d9"), Color("white")]
```

### Color Comparison

#### Sane Default

Color comparison is a vast subject. However, it might seem quite straightforward for you. `Color` uses a configurable default way of comparing color that might suit your needs:

```
>>> Color("red") == Color("#f00") == Color("blue", hue=0)
True
```

The default comparison algorithm focuses only on the "web" representation which is equivalent to comparing the long hex representation (e.g. #FF0000) or to be more specific, it is equivalent to compare the amount of red, green, and blue composition of the RGB representation, each of these value being quantized to a 256 value scale.

This default comparison is a practical and convenient way to measure the actual color equivalence on your screen, or in your video card memory.

But this comparison wouldn't make the difference between a black red, and a black blue, which both are black:

```
>>> black_red = Color("red", lightness=0)
>>> black_blue = Color("blue", lightness=0)

>>> black_red == black_blue
True
```

#### Customization

But, this is not the sole way to compare two colors. As I'm quite lazy, I'm providing you a way to customize it to your needs. Thus:

```
>>> from colourings import RGB_equivalence, HSL_equivalence
>>> black_red = Color("red", lightness=0, equality=HSL_equivalence)
>>> black_blue = Color("blue", lightness=0, equality=HSL_equivalence)

>>> black_red == black_blue
False
```

As you might have already guessed, the sane default is `RGB_equivalence`, so:

```
>>> black_red = Color("red", lightness=0, equality=RGB_equivalence)
>>> black_blue = Color("blue", lightness=0, equality=RGB_equivalence)

>>> black_red == black_blue
True
```

Here's how you could implement your unique comparison function:

```
>>> saturation_equivalence = lambda c1, c2: c1.saturation == c2.saturation
>>> red = Color("red", equality=saturation_equivalence)
>>> blue = Color("blue", equality=saturation_equivalence)
>>> white = Color("white", equality=saturation_equivalence)

>>> red == blue
True
>>> white == red
False
```

Note: When comparing 2 colors, only the equality function of the first color will be used. Thus:

```
>>> black_red = Color("red", luminance=0, equality=RGB_equivalence)
>>> black_blue = Color("blue", luminance=0, equality=HSL_equivalence)

>>> black_red == black_blue
True
```
But reverse operation is not equivalent !:

```
>>> black_blue == black_red
False
```

### Equality to Non-`Color` Objects
As a side note, whatever your custom equality function is, it won't be used if you compare to anything else than a `Color` instance:

```
>>> red = Color("red", equality=lambda c1, c2: True)
>>> blue = Color("blue", equality=lambda c1, c2: True)
```
Note that these instances would compare as equal to any other color:

```
>>> red == blue
True
```

But on another non-`Color` object:

```
>>> red == None
False
>>> red != None
True
```

Actually, `Color` instances will, politely enough, leave the other side of the equality have a chance to decide of the output, (by executing its own __eq__), so:

```
>>> class OtherColorImplem():
...     def __init__(self, color):
...         self.color = color
...     def __eq__(self, other):
...         return self.color == other.web

>>> alien_red = OtherColorImplem("red")
>>> red == alien_red
True
>>> blue == alien_red
False
```

And inequality (using __ne__) are also polite:

```
>>> class AnotherColorImplem(OtherColorImplem):
...     def __ne__(self, other):
...         return self.color != other.web

>>> new_alien_red = AnotherColorImplem("red")
>>> red != new_alien_red
False
>>> blue != new_alien_red
True
```

## Picking Arbitrary Color for a Python Object
### Basic Usage
Sometimes, you just want to pick a color for an object in your application often to visually identify this object. Thus, the picked color should be the same for same objects, and different for different object:

```
>>> foo = object()
>>> bar = object()

>>> Color(pick_for=foo)
<Color ...>
>>> Color(pick_for=foo) == Color(pick_for=foo)
True
>>> Color(pick_for=foo) == Color(pick_for=bar)
False
```

Of course, although there's a tiny probability that different strings yield the same color, most of the time, different inputs will produce different colors.

#### Advanced Usage
You can customize your color picking algorithm by providing a picker. A picker is a callable that takes an object, and returns something that can be instantiated as a color by Color:

```
>>> my_picker = lambda obj: "red" if isinstance(obj, int) else "blue"
>>> Color(pick_for=3, picker=my_picker, pick_key=None)
<Color red>
>>> Color(pick_for="foo", picker=my_picker, pick_key=None)
<Color blue>
```

You might want to use a particular picker, but enforce how the picker will identify two object as the same (or not). So there's a pick_key attribute that is provided and defaults as equivalent of hash method and if hash is not supported by your object, it'll default to the str of your object salted with the class name.

Thus:

```
>>> class MyObj(str): pass
>>> my_obj_color = Color(pick_for=MyObj("foo"))
>>> my_str_color = Color(pick_for="foo")
>>> my_obj_color == my_str_color
False
```

Please make sure your object is hashable or "stringable" before using the RGB_color_picker picking mechanism or provide another color picker. Nearly all python object are hashable by default so this shouldn't be an issue (e.g. instances of object and subclasses are hashable).

Neither hash nor str are perfect solution. So feel free to use pick_key at Color instantiation time to set your way to identify objects, for instance:

```
>>> a = object()
>>> b = object()
>>> Color(pick_for=a, pick_key=id) == Color(pick_for=b, pick_key=id)
False
```

When choosing a pick key, you should closely consider if you want your color to be consistent between runs (this is NOT the case with the last example), or consistent with the content of your object if it is a mutable object.

Default value of pick_key and picker ensures that the same color will be attributed to same object between different run on different computer for most python object.

### Color Factory
As you might have noticed, there are few attributes that you might want to see attached to all of your colors as equality for equality comparison support, or picker, pick_key to configure your object color picker.

You can create a customized Color factory thanks to the make_color_factory:

```
>>> from colourings import make_color_factory, HSL_equivalence, RGB_color_picker

>>> get_color = make_color_factory(
...    equality=HSL_equivalence,
...    picker=RGB_color_picker,
...    pick_key=str,
... )
```

All color created thanks to CustomColor class instead of the default one would get the specified attributes by default:

```
>>> black_red = get_color("red", luminance=0)
>>> black_blue = get_color("blue", luminance=0)
Of course, these are always instances of Color class:

>>> isinstance(black_red, Color)
True
Equality was changed from normal defaults, so:

>>> black_red == black_blue
False
```

This because the default equivalence of Color was set to HSL_equivalence.

## Contributing
Any suggestion or issue is welcome. Push request are very welcome, please check out the guidelines.
