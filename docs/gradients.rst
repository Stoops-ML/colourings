Gradients and colour scales
===========================

Between two colours
-------------------

.. code-block:: python

   from colourings import Color

   red = Color("red")
   blue = Color("blue")

   print(list(red.range_to(blue, 5)))
   # [<Color red>, <Color #ff007f>, <Color magenta>, <Color #7f00ff>, <Color blue>]

   print(list(red.range_to(blue, 5, longer=True)))
   # [<Color red>, <Color yellow>, <Color lime>, <Color cyan>, <Color blue>]

``longer`` takes the other way around the hue circle.

Multi-stop scales
-----------------

.. code-block:: python

   from colourings import Color, color_scale

   stops = (Color("black"), Color("orange"), Color("blue"), Color("white"))
   palette = color_scale(stops, 10)

   for color in palette:
       print(color)
   # black #39221c #8e4d1c orange #ff003c #e100ff blue #bd71e3 #e3c6d9 white

``color_scale`` requires at least two colours and ``num_steps >=
len(colors)``. Every stop appears in the result, so the anchors you asked for
are the anchors you get.

Choosing the interpolation space
--------------------------------

Both ``color_scale`` and ``range_to`` take a ``space``: one of ``hsl``,
``lab``, ``lch``, ``oklab`` or ``oklch``.

It defaults to ``hsl``, which is what these functions have always used, but
**``hsl`` is the weakest of the five for a gradient**. It is polar, so it
swings through hues that are in neither endpoint, and its lightness is not a
perceptual quantity, so the steps come out unevenly spaced.

.. code-block:: python

   from colourings import Color

   red = Color("red")

   print(list(red.range_to("cyan", 5)))
   # HSL invents a magenta and a violet that are in neither endpoint.
   # [<Color red>, <Color #ff00bf>, <Color #7f00ff>, <Color #0040ff>, <Color cyan>]

   print(list(red.range_to("cyan", 5, space="oklab")))
   # Oklab blends the two, in evenly sized perceptual steps.
   # [<Color red>, <Color #ee745b>, <Color #d2a993>, <Color #a3d6c9>, <Color cyan>]

Reach for ``oklab``. It is perceptually uniform, so its steps are evenly
spaced, and rectangular, so there is no hue arc to sweep. Use ``oklch`` when
that sweep is the point, and ``lab`` or ``lch`` for the CIE equivalents.

The default is ``hsl`` only because changing it would move every existing
caller's output. ``Color.mix`` -- which is newer -- defaults to ``oklab``.

``longer`` needs a hue
----------------------

``longer`` chooses the arc around the hue circle, so it applies only to a
space that has one. Passing it with a rectangular space raises rather than
being ignored:

.. code-block:: python

   from colourings import Color

   try:
       Color("red").range_to("blue", 5, space="oklab", longer=True)
   except ValueError as e:
       print(e)
   # 'longer' selects the arc around a hue circle, and 'oklab' has no hue channel. Use hsl, lch or oklch, or drop 'longer'.

Alpha
-----

Alpha is interpolated alongside the colour, so a scale can fade as well as
shift. It belongs to no colour space, so ``space`` does not apply to it and it
is always interpolated linearly:

.. code-block:: python

   from colourings import Color

   opaque = Color("red", alpha=1.0)
   clear = Color("blue", alpha=0.0)
   print([c.alpha for c in opaque.range_to(clear, 5)])  # [1.0, 0.75, 0.5, 0.25, 0.0]

A scale between colours that are all opaque is unaffected. The endpoints keep
their alpha exactly, so a scale ending on a colour reproduces it.

Gamut
-----

A straight line between two saturated colours can leave the sRGB gamut. Those
points are clamped, as everywhere else in the library, so a scale through one
of them is a shade off the exact interpolant. :doc:`ranges` explains how to
check a colour before relying on it.