Adjusting a colour
==================

Every method here returns a **new** colour and leaves the original alone,
carrying its alpha across.

.. code-block:: python

   from colourings import Color

   c = Color("#3d7ab8")

   c.lighten(0.2)   # and darken, saturate, desaturate
   c.rotate_hue(180)
   c.grayscale()    # the same method as greyscale()
   c.invert()
   c.mix("white", 0.3)

Absolute and relative steps
---------------------------

``lighten``, ``darken``, ``saturate`` and ``desaturate`` take an amount in
``[0, 1]`` and a ``relative`` flag that decides how to read it:

**relative** (the default)
   A fraction of the distance still available. A step can never clip, and
   ``1.0`` lands exactly on the limit -- so ``lighten(1.0)`` is white and
   ``darken(1.0)`` is black.

**absolute** (``relative=False``)
   A fraction of the whole range, added flat and clamped. This is what Sass's
   ``lighten()`` does.

.. code-block:: python

   from colourings import Color

   Color("#e0e0e0").lightness                          # 87.84...
   Color("#e0e0e0").lighten(0.1).lightness             # 89.058..., a tenth of what was left
   Color("#e0e0e0").lighten(0.1, relative=False).lightness  # 97.84..., a flat +10

These move HSL lightness and saturation, which are geometric rather than
perceptual quantities. For a step that looks the same size wherever it starts,
``mix`` toward white or black in ``oklab`` instead.

``grayscale`` is not ``desaturate(1.0)``
----------------------------------------

They produce different greys, and the difference is large:

.. code-block:: python

   from colourings import Color

   Color("blue").desaturate(1.0)  # <Color #7f7f7f>, holds HSL lightness
   Color("blue").grayscale()      # <Color #4c4c4c>, holds luminance
   Color("yellow").grayscale()    # <Color #f7f7f7>

Desaturating holds HSL lightness, so **every** fully saturated colour
collapses to the same mid grey whatever its brightness -- blue and yellow both
become ``#7f7f7f``. ``grayscale`` holds relative luminance exactly, so blue
stays dark and yellow stays bright.

Use ``grayscale`` when the grey has to stand in for the colour, which is
almost always what is wanted.

Mixing
------

.. code-block:: python

   from colourings import Color

   Color("red").mix("blue")                  # <Color #8c53a2>, halfway in oklab
   Color("red").mix("blue", 0.25)            # <Color #c6496d>
   Color("red").mix("blue", 0.5, space="hsl")  # <Color magenta>

``mix`` defaults to ``oklab``, unlike ``color_scale``, which defaults to
``hsl`` only because changing it would move every existing caller's output.

Alpha is blended too, so mixing an opaque colour with a transparent one fades.
For the CSS spelling of the same idea, with its own percentage rules, see
``color-mix()`` in :doc:`css`.

Hue
---

.. code-block:: python

   from colourings import Color

   Color("red").rotate_hue(120)  # <Color lime>
   Color("red").invert()         # <Color cyan>

``invert`` inverts the RGB channels, which is not the same as rotating the hue
by 180 degrees -- inverting also flips lightness.

Harmonies
---------

Hue relationships, as new colours carrying this one's alpha:

.. code-block:: python

   from colourings import Color

   Color("red").complementary()  # <Color cyan>
   Color("red").triadic()        # (<Color red>, <Color lime>, <Color blue>)
   Color("red").tetradic()
   # (<Color red>, <Color chartreuse>, <Color cyan>, <Color #7f00ff>)
   Color("red").analogous()      # (<Color #ff007f>, <Color red>, <Color #ff7f00>)
   Color("red").analogous(60)    # (<Color magenta>, <Color red>, <Color yellow>)

The base colour is included, and ``analogous`` puts it in the middle, so each
result reads in wheel order.