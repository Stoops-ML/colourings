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

.. code-block:: python

   from colourings import Color

   c1 = Color("red")
   c2 = Color("#f00")
   c3 = Color(rgb=(255, 0, 0))
   c4 = Color(hsl=(0, 100, 50))

   print(c1 == c2 == c3 == c4)  # True

Read and update channels
------------------------

.. code-block:: python

   from colourings import Color

   color = Color("blue")
   print(color.hsla)  # (240.0, 100.0, 50.0, 100.0)

   color.hue = 0
   color.saturation = 50
   color.lightness = 75
   color.alpha = 0.5

   print(color.hsla)   # (0.0, 50.0, 75.0, 50.0)
   print(color.rgbaf)  # (0.875, 0.625, 0.625, 0.5)

Interpolate between colors
--------------------------

.. code-block:: python

   from colourings import Color

   red = Color("red")
   blue = Color("blue")

   # Shortest hue path.
   print(list(red.range_to(blue, 5)))

   # Longer hue path around the wheel.
   print(list(red.range_to(blue, 5, longer=True)))

Build a multi-stop color scale
------------------------------

.. code-block:: python

   from colourings import Color, color_scale

   palette = color_scale((Color("black"), Color("orange"), Color("white")), 6)
   for swatch in palette:
       print(swatch)

Use conversion helpers directly
------------------------------

.. code-block:: python

   from colourings.conversions import hsl2web, rgb2hex, rgb2hsl, web2rgb

   print(rgb2hex((255, 0, 0)))      # #f00
   print(rgb2hsl((255, 0, 0)))      # (0.0, 100.0, 50.0)
   print(web2rgb("rebeccapurple"))  # (102.0, 51.0, 153.0)
   print(hsl2web((0, 0, 50.2)))     # gray

Notes on value ranges
---------------------

The library uses explicit ranges for each representation:

* ``rgb`` channels are in ``[0, 255]``
* ``rgbf`` channels are in ``[0, 1]``
* ``hsl`` uses ``hue in [0, 360]`` and saturation/lightness in ``[0, 100]``
* ``alpha`` is exposed on ``Color.alpha`` in ``[0, 1]``
