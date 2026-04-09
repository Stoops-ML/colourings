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
   print(blue.rgb)      # (0.0, 0.0, 255.0)
   print(blue.hsl)      # (240.0, 100.0, 50.0)

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
   print(c.hsla)  # (240.0, 100.0, 50.0, 100.0)

   # Update
   c.hue = 0
   c.saturation = 50
   c.lightness = 75
   c.alpha = 0.5

   print(c.hsla)   # (0.0, 50.0, 75.0, 50.0)
   print(c.rgbaf)  # (0.875, 0.625, 0.625, 0.5)

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

Use conversion helpers directly
------------------------------

.. code-block:: python

   from colourings.conversions import hsl2web, rgb2hex, rgb2hsl, web2rgb

   print(rgb2hex((255, 0, 0)))      # #f00
   print(rgb2hsl((255, 0, 0)))      # (0.0, 100.0, 50.0)
   print(web2rgb("rebeccapurple"))  # (102.0, 51.0, 153.0)
   print(hsl2web((0, 0, 50.2)))     # gray

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

   print(HSL.BLUE)   # (240.0, 100.0, 50.0)
   print(RGB.BLUE)   # (0.0, 0.0, 255.0)
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
* ``Color.alpha`` is always in ``[0, 1]``
