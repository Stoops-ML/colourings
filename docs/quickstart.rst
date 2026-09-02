Quick start
===========

A ten-minute tour. Each section links to the page that covers it properly.

One object, many formats
------------------------

A ``Color`` stores one colour and exposes every format as a property. Reading
one converts; assigning one converts back.

.. code-block:: python

   from colourings import Color

   blue = Color("blue")
   print(blue)        # blue
   print(blue.hex)    # #00f
   print(blue.hex_l)  # #0000ff
   print(blue.rgb)    # RGB(red=0.0, green=0.0, blue=255.0)
   print(blue.hsl)    # HSL(hue=240.0, saturation=100.0, lightness=50.0)

   blue.red = 255
   print(blue.web)    # magenta

The tuple properties are named tuples, so components can be read by name and
still behave as plain tuples:

.. code-block:: python

   c = Color("red")
   c.rgb.red      # 255.0
   c.hsl.hue      # 0.0
   c.rgbaf.alpha  # 1.0

Build one from anything
-----------------------

All of these are the same red:

.. code-block:: python

   from colourings import Color

   Color("red")
   Color("#f00")
   Color(rgb=(255, 0, 0))
   Color(hsl=(0, 100, 50))
   Color(oklch=(0.62796, 0.25768, 29.2339))
   Color("rgb(255 0 0)")
   Color("color-mix(in oklab, red, red)")

Fifteen input formats, CSS syntax, and a keyword to set a property as you
build. See :doc:`colors`.

.. code-block:: python

   Color("red", lightness=0).hsl  # HSL(hue=0.0, saturation=100.0, lightness=0.0)

Adjust it
---------

Every adjustment returns a new colour and leaves the original alone:

.. code-block:: python

   from colourings import Color

   c = Color("#3d7ab8")

   c.lighten(0.2).hex_l   # '#6095ca'
   c.rotate_hue(180)      # <Color #b87b3d>
   c.mix("white", 0.3)    # <Color #78a2cf>
   c.grayscale().hex_l    # '#777777'

See :doc:`adjusting`.

Make a gradient
---------------

.. code-block:: python

   from colourings import Color, color_scale

   red = Color("red")
   print(list(red.range_to("cyan", 5, space="oklab")))
   # [<Color red>, <Color #ee745b>, <Color #d2a993>, <Color #a3d6c9>, <Color cyan>]

   stops = (Color("black"), Color("orange"), Color("blue"), Color("white"))
   for color in color_scale(stops, 10):
       print(color)
   # black #39221c #8e4d1c orange #ff003c #e100ff blue #bd71e3 #e3c6d9 white

Pick the interpolation ``space`` deliberately -- ``oklab`` is usually the right
answer and ``hsl`` is the default only for backwards compatibility. See
:doc:`gradients`.

Measure it
----------

.. code-block:: python

   from colourings import Color

   Color("black").contrast_ratio("white")  # 21.0
   Color("#767676").is_readable("white")   # True
   Color("navy").best_text_color()         # <Color white>
   Color("black").delta_e("white")         # 100.0
   Color("#123456").nearest_name()         # 'midnightblue'

WCAG contrast is in :doc:`contrast`; perceptual distance and the four delta-E
metrics are in :doc:`difference`.

Read and write CSS
------------------

.. code-block:: python

   from colourings import Color

   Color("rgb(255 0 0 / 50%)").alpha       # 0.5
   Color("color-mix(in oklab, red, blue)") # <Color #8c53a2>
   Color("color(display-p3 0.4 0.5 0.6)")  # <Color #5f809c>

   Color("red", alpha=0.5).to_css("rgb")   # 'rgb(255 0 0 / 0.5)'
   Color("red").to_css("oklch")            # 'oklch(0.62796 0.25768 29.23389)'

See :doc:`css`.

Handle a bad value
------------------

Everything caused by a value that is not a usable colour derives from
``ColorError``, and a near miss says what it was near:

.. code-block:: python

   from colourings import Color, ColorError

   try:
       Color("chartruese")
   except ColorError as e:
       print(f"not a color: {e}")
   # not a color: Cannot identify color 'chartruese'. Did you mean 'chartreuse'?

See :doc:`errors`.

The one thing to know
---------------------

A ``Color`` holds sRGB. ``lab``, ``lch``, ``oklab``, ``oklch``, ``xyz`` and
``yuv`` can each name a colour that sRGB cannot show, and such a value is
**clipped** on the way in -- quietly, and often. Afterwards it is
indistinguishable from a colour that always fitted, so ask first:

.. code-block:: python

   from colourings import in_srgb_gamut

   in_srgb_gamut((53.2408, 80.0925, 67.2032), "lab")  # True, this is red
   in_srgb_gamut((100, 120, -120), "lab")             # False, would be clipped

:doc:`ranges` covers this in full, and it is worth the five minutes.