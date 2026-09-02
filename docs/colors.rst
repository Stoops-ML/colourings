Creating and reading colours
============================

Every input format
------------------

All of these produce equivalent red colours:

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
   Color(oklab=(0.62796, 0.22486, 0.12585))
   Color(oklch=(0.62796, 0.25768, 29.2339))
   Color(xyz=(41.2456, 21.2673, 1.9334))
   Color(cmyk=(0, 100, 100, 0))
   Color(yuv=(0.299, -0.147108, 0.614777))
   Color(Color("red"))
   Color("rgb(255 0 0)")   # and the other CSS forms
   Color("#ff000080")      # hex with alpha

Only one colour input source is allowed per call. Passing two raises
``ValueError``, since it is a mistake about the call rather than about a
colour.

Alpha when copying
------------------

Copying a colour carries its alpha across. An explicit ``alpha`` overrides the
copied one rather than having to agree with it, so ``Color(other, alpha=0.5)``
works for any ``other``:

.. code-block:: python

   from colourings import Color

   translucent = Color(rgba=(255, 0, 0, 128))
   Color(translucent).alpha              # 0.502
   Color(translucent, alpha=0.25).alpha  # 0.25

Bare sequences
--------------

A sequence with no keyword is identified from its length and its component
ranges, and a four-component one keeps the alpha it carries:

.. code-block:: python

   from colourings import Color

   Color((255, 200, 200))       # RGB
   Color((255, 200, 200, 128))  # RGBA, alpha 0.502

That works only where the ranges tell the formats apart. ``(0, 0, 0)`` is
equally valid RGB and HSL, so it raises ``AmbiguousColorError`` -- name the
format to settle it:

.. code-block:: python

   from colourings import AmbiguousColorError, Color

   try:
       Color((0, 0, 0))
   except AmbiguousColorError as e:
       print(e)
   # Cannot determine whether color is RGB or HSL.

Setting properties as you build
-------------------------------

Any remaining keyword sets a writable property once the colour is built, which
is how you say "this colour, but darker" in one call:

.. code-block:: python

   from colourings import Color

   Color("red", lightness=0).hsl  # HSL(hue=0.0, saturation=100.0, lightness=0.0)

Each goes through its own setter, so it is validated exactly as an assignment
would be, and ``Color("red", lightness=200)`` raises.

This is not a way to attach arbitrary attributes. ``Color`` defines
``__slots__``, so an unknown name raises ``AttributeError`` instead of quietly
becoming one:

.. code-block:: python

   from colourings import Color

   try:
       Color("red", lightnes=50)  # a typo
   except AttributeError:
       print("rejected, rather than silently becoming an attribute")
   # rejected, rather than silently becoming an attribute

The message is CPython's own, and its wording has changed twice across
supported versions, so it is not quoted here.

A subclass that does not redeclare ``__slots__`` has a ``__dict__``, and does
accept any name.

Reading and updating channels
-----------------------------

Individual channels are readable and writable, and an assignment converts back
into the stored HSL:

.. code-block:: python

   from colourings import Color

   c = Color("blue")

   c.hue, c.saturation, c.lightness  # (240.0, 100.0, 50.0)
   c.red, c.green, c.blue            # (0.0, 0.0, 255.0)
   c.alpha                           # 1.0

   c.hue = 0
   c.saturation = 50
   c.lightness = 75
   c.alpha = 0.5

   c.hsla   # HSLA(hue=0.0, saturation=50.0, lightness=75.0, alpha=50.0)
   c.rgbaf  # RGBAf(red=0.875, green=0.625, blue=0.625, alpha=0.5)

Note that ``alpha`` is always in ``[0, 1]`` while ``hsla``'s fourth component
is on the ``[0, 100]`` scale that format uses. :doc:`ranges` lists every scale.

Named components
----------------

The tuple properties, and the conversion functions, return named tuples:

.. code-block:: python

   from colourings import Color
   from colourings.definitions import RGB

   c = Color("red")

   print(c.rgb.red)      # 255.0
   print(c.hsl.hue)      # 0.0
   print(c.rgbaf.alpha)  # 1.0

They are still ordinary tuples, so comparing, unpacking, indexing and hashing
against plain tuples all behave as before, and assignment still accepts any
sequence:

.. code-block:: python

   r, g, b = c.rgb
   assert c.hsl == (0.0, 100.0, 50.0)
   assert isinstance(c.rgb, RGB)

   c.rgb = (0.0, 0.0, 255.0)

The types are ``RGB``, ``RGBA``, ``HSL``, ``HSLA``, ``HSV``, ``XYZ``, ``LAB``,
``LCH``, ``OKLAB``, ``OKLCH``, ``CMYK``, ``YUV`` and the normalised ``RGBf``,
``RGBAf``, ``HSLf`` and ``HSLAf``, all importable from
``colourings.definitions``.

.. note::

   These are distinct from the same-named accessor objects that look up
   colours by name, which live in ``colourings.colour`` and are called
   ``NAMED_RGB``, ``NAMED_HSL`` and ``NAMED_HEX``. They were renamed because
   they shadowed these tuple types.

Named-colour accessors and the British spelling
-----------------------------------------------

.. code-block:: python

   from colourings import Colour
   from colourings.colour import NAMED_HEX, NAMED_HSL, NAMED_RGB

   print(NAMED_HSL.BLUE)  # HSL(hue=240.0, saturation=100.0, lightness=50.0)
   print(NAMED_RGB.BLUE)  # RGB(red=0.0, green=0.0, blue=255.0)
   print(NAMED_HEX.BLUE)  # #00f

   assert Colour("red") == Colour("#f00")

``Colour`` is ``Color`` -- the same class under the British spelling, not a
subclass of it, so ``Colour is Color`` is ``True`` and a ``Colour`` stays one
through a scale.

Attribute lookup on the accessors is case-insensitive and accepts the
canonical spelling:

.. code-block:: python

   from colourings.colour import NAMED_HEX

   NAMED_HEX.rebeccapurple == NAMED_HEX.RebeccaPurple  # True