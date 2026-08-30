Quick Start
===========

Basic usage
-----------

.. code-block:: python

   from colourings import Color

   blue = Color("blue")
   print(blue)          # blue
   print(blue.hex)      # #00f
   print(blue.hex_l)    # #0000ff
   print(blue.rgb)      # RGB(red=0.0, green=0.0, blue=255.0)
   print(blue.hsl)      # HSL(hue=240.0, saturation=100.0, lightness=50.0)

Create colors from different inputs
-----------------------------------

All of the following produce equivalent red colors:

.. code-block:: python

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
   Color(xyz=(41.2456, 21.2673, 1.9334))
   Color(cmyk=(0, 100, 100, 0))
   Color(yuv=(0.299, -0.147108, 0.614777))
   Color(Color("red"))

Read and update channels
------------------------

.. code-block:: python

   from colourings import Color

   c = Color("blue")

   # Read individual channels
   print(c.hue, c.saturation, c.lightness)
   print(c.red, c.green, c.blue)
   print(c.alpha)
   print(c.hsla)  # HSLA(hue=240.0, saturation=100.0, lightness=50.0, alpha=100.0)

   # Update
   c.hue = 0
   c.saturation = 50
   c.lightness = 75
   c.alpha = 0.5

   print(c.hsla)   # HSLA(hue=0.0, saturation=50.0, lightness=75.0, alpha=50.0)
   print(c.rgbaf)  # RGBAf(red=0.875, green=0.625, blue=0.625, alpha=0.5)

Interpolate between colors
--------------------------

.. code-block:: python

   from colourings import Color

   red = Color("red")
   blue = Color("blue")

   # Shortest hue path.
   print(list(red.range_to(blue, 5)))
   # [<Color red>, <Color #ff007f>, <Color magenta>, <Color #7f00ff>, <Color blue>]

   # Longer hue path around the wheel.
   print(list(red.range_to(blue, 5, longer=True)))
   # [<Color red>, <Color yellow>, <Color lime>, <Color cyan>, <Color blue>]

Build a multi-stop color scale
------------------------------

.. code-block:: python

   from colourings import Color, color_scale

   palette = color_scale((Color("black"), Color("orange"), Color("white")), 6)
   for swatch in palette:
       print(swatch)

   # Multi-stop scale with four anchor colors:
   stops = (Color("black"), Color("orange"), Color("blue"), Color("white"))
   palette = color_scale(stops, 10)
   for color in palette:
       print(color)
   # black #39221c #8e4d1c orange #ff003c #e100ff blue #bd71e3 #e3c6d9 white

Named components
----------------

Conversions and the ``Color`` tuple attributes return named tuples, so
components can be read by name:

.. code-block:: python

   from colourings import Color
   from colourings.definitions import RGB

   c = Color("red")

   print(c.rgb.red)      # 255.0
   print(c.hsl.hue)      # 0.0
   print(c.rgbaf.alpha)  # 1.0

They are still ordinary tuples, so comparing, unpacking, indexing and hashing
against plain tuples behave exactly as before, and assignment still accepts any
sequence:

.. code-block:: python

   r, g, b = c.rgb
   assert c.hsl == (0.0, 100.0, 50.0)
   assert isinstance(c.rgb, RGB)

   c.rgb = (0.0, 0.0, 255.0)

The types are ``RGB``, ``RGBA``, ``HSL``, ``HSLA`` and their normalised
``RGBf``, ``RGBAf``, ``HSLf`` and ``HSLAf`` counterparts, all importable from
``colourings.definitions``. Note these are distinct from the same-named
``colourings.colour.HSL`` and ``colourings.colour.RGB`` accessor objects that
look up colors by name.

Use conversion helpers directly
------------------------------

.. code-block:: python

   from colourings.conversions import hsl2web, rgb2hex, rgb2hsl, web2rgb

   print(rgb2hex((255, 0, 0)))      # #f00
   print(rgb2hsl((255, 0, 0)))      # HSL(hue=0.0, saturation=100.0, lightness=50.0)
   print(web2rgb("rebeccapurple"))  # RGB(red=102.0, green=51.0, blue=153.0)
   print(hsl2web((0, 0, 50.2)))     # gray

Cached conversions
------------------

Conversions are memoized with a bounded LRU cache, so repeated lookups of the
same color are served from the cache. Results are immutable, so callers may
share them safely, and repeated calls return the identical object:

.. code-block:: python

   from colourings.conversions import clear_caches, rgb2hsl

   assert rgb2hsl((255, 0, 0)) is rgb2hsl((255, 0, 0))

   clear_caches()  # release cached results; never needed for correctness

Work in a perceptual space
--------------------------

``lab`` and ``lch`` are perceptually uniform, so they are the ones to
interpolate or measure distance in. ``lch`` is ``lab`` in polar form, which
makes it convenient for adjusting lightness or chroma without shifting hue:

.. code-block:: python

   from colourings import Color

   c = Color("rebeccapurple")
   lighter = Color(lch=(c.lch.lightness + 20, c.lch.chroma, c.lch.hue))

The CIE conversions use the D65 illuminant, which sRGB is defined against, so
values are not interchangeable with a library that uses D50. Converting into
sRGB clamps anything outside its gamut.

Handle errors
-------------

Every failure caused by a value that is not a usable color derives from
``ColorError``:

.. code-block:: python

   from colourings import Color, ColorError

   try:
       Color("nope")
   except ColorError as e:
       print(f"not a color: {e}")

``InvalidColorError`` covers a value invalid in the format it was given as,
``AmbiguousColorError`` a value that reads as more than one format, and
``UnknownColorError`` a value matching no supported format. ``ColorError``
derives from both ``ValueError`` and ``TypeError``, so existing ``except``
clauses keep working.

Equality behavior
-----------------

By default, ``Color`` equality compares the hex-rendered color:

.. code-block:: python

   from colourings.colour import Color

   assert Color("red") == Color("#f00")

You can plug in a custom comparison function:

.. code-block:: python

   from colourings.colour import Color, HSL_equivalence

   c1 = Color("red", lightness=0, equality=HSL_equivalence)
   c2 = Color("blue", lightness=0, equality=HSL_equivalence)

   print(c1 == c2)  # False

Comparing against anything that is not a color is ``False`` rather than an
error, and colors are hashable:

.. code-block:: python

   assert Color("red") != "red"
   assert len({Color("red"), Color("#f00"), Color("blue")}) == 2

``==`` consults both operands' strategies, so it is symmetric even when the two
colors carry different ones. The hash follows ``hex_l``, matching both built-in
strategies. ``Color`` is mutable, so do not mutate one while it is held in a
set or used as a dict key.

Deterministic color picking
---------------------------

Use ``pick_for`` to map Python objects to stable colors:

.. code-block:: python

   from colourings.colour import Color

   print(Color(pick_for="user:123").web)  # #010000
   print(Color(pick_for="user:123") == Color(pick_for="user:123"))  # True

You can override the picking strategy with:

- ``picker``: callable that returns a color-like value
- ``pick_key``: callable that maps objects to comparable keys

Convenience objects and aliases
-------------------------------

.. code-block:: python

   from colourings.colour import HEX, HSL, RGB, Colour

   print(HSL.BLUE)   # HSL(hue=240.0, saturation=100.0, lightness=50.0)
   print(RGB.BLUE)   # RGB(red=0.0, green=0.0, blue=255.0)
   print(HEX.BLUE)   # #00f

   assert Colour("red") == Colour("#f00")

``Colour`` is an alias subclass of ``Color`` for British spelling preference.

Notes on value ranges
---------------------

The library uses explicit ranges for each representation:

* ``rgb`` / ``rgba`` channels are in ``[0, 255]``
* ``rgbf`` / ``rgbaf`` channels are in ``[0, 1]``
* ``hsl`` uses ``hue in [0, 360]`` and saturation/lightness in ``[0, 100]``
* ``hsla`` is the same as ``hsl`` with alpha in ``[0, 100]``
* ``hslf`` / ``hslaf`` channels are in ``[0, 1]``
* ``hsv`` uses ``hue in [0, 360]`` and saturation/value in ``[0, 100]``
* ``xyz`` is CIE XYZ under D65, scaled so that white has ``y`` of 100
* ``lab`` has lightness in ``[0, 100]`` and a/b in ``[-128, 127]``
* ``lch`` has chroma in ``[0, 182]`` and hue in ``[0, 360]``
* ``cmyk`` channels are in ``[0, 100]``
* ``yuv`` is BT.601, luma in ``[0, 1]``
* ``Color.alpha`` is always in ``[0, 1]``
