CSS syntax
==========

Colours can be read from, and written back to, the syntax CSS uses.

Reading
-------

.. code-block:: python

   from colourings import Color

   Color("rgb(255, 0, 0)")               # legacy commas
   Color("rgb(255 0 0 / 50%)")           # CSS Color 4, alpha after a slash
   Color("hsl(0deg 100% 50%)")           # deg, grad, rad and turn all work
   Color("oklch(0.62796 0.25768 29.23389)")
   Color("#ff000080")                    # an 8-digit hex, and #RGBA
   Color("transparent")                  # black with no alpha

``rgb``, ``rgba``, ``hsl``, ``hsla``, ``lab``, ``lch``, ``oklab`` and
``oklch`` are read, with either comma or space separators, in any case, and
with surrounding whitespace ignored.

Writing
-------

.. code-block:: python

   from colourings import Color

   Color("red").to_css()                  # '#f00'
   Color("red", alpha=0.5).to_css("rgb")  # 'rgb(255 0 0 / 0.5)'
   Color("red").to_css("hsl")             # 'hsl(0 100% 50%)'
   Color("red").to_css("oklch")           # 'oklch(0.62796 0.25768 29.23389)'

Output uses the space-separated syntax a browser itself serialises to, and
includes the alpha only when the colour is not opaque. Every form round-trips
exactly: reading back what ``to_css`` wrote gives the same 8-bit colour, alpha
included.

Out of range is an error, not a clamp
-------------------------------------

A browser reads ``rgb(300 0 0)`` as red. Here it raises:

.. code-block:: python

   from colourings import Color, InvalidColorError

   try:
       Color("rgb(300 0 0)")
   except InvalidColorError as e:
       print(e)
   # Input is not an RGB type.

Quietly turning one colour into another is what this library avoids
everywhere, and reading a stylesheet is not a reason to start. This is the one
place the library refuses rather than clipping, and the reason is that the
number was *written down* rather than computed -- so a value out of range is a
mistake worth reporting, not a result to round off.

Percentage references
---------------------

Percentages scale against a different reference in each function. This is what
CSS Color 4 specifies rather than anything this library chose:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - function
     - axis
     - ``100%``
   * - ``rgb()``
     - ``r``, ``g``, ``b``
     - 255
   * - ``hsl()``
     - ``s``, ``l``
     - 100
   * - ``lab()``, ``lch()``
     - ``L``
     - 100
   * - ``lab()``
     - ``a``, ``b``
     - ±125
   * - ``lch()``
     - ``C``
     - 150
   * - ``oklab()``, ``oklch()``
     - ``L``
     - 1
   * - ``oklab()``
     - ``a``, ``b``
     - ±0.4
   * - ``oklch()``
     - ``C``
     - 0.4

So ``oklch(0.5 50% 200)`` is exactly ``oklch(0.5 0.2 200)``:

.. code-block:: python

   from colourings import Color

   Color("oklch(0.5 50% 200)") == Color("oklch(0.5 0.2 200)")  # True

``100%`` is the reference and not a maximum: a larger percentage is allowed by
the syntax and then refused by the range check, exactly as the equivalent
number is.

System colours
--------------

``Canvas``, ``ButtonFace``, ``LinkText`` and the rest are recognised and
deliberately **not** resolved. CSS defines each as whatever the reader's
platform, browser and theme make it, so any fixed value would be wrong for
most readers and right for nobody.

.. code-block:: python

   from colourings import Color, UnknownColorError

   try:
       Color("Canvas")
   except UnknownColorError as e:
       print(e)
   # 'canvas' is a CSS system color, whose value is whatever the reader's platform
   # and theme make it, so there is no fixed color to return. Name the color you
   # mean instead.

Saying that is more useful than reporting it as an unidentifiable typo. The
deprecated ones from the specification's appendix -- ``ThreeDShadow``,
``InfoBackground`` and the rest -- are recognised the same way. The full set is
``colourings.definitions.SYSTEM_COLORS``.

``color-mix()``
---------------

.. code-block:: python

   from colourings import Color

   Color("color-mix(in oklab, red, blue)")           # <Color #8c53a2>
   Color("color-mix(red, blue)")                     # the same: oklab is the default
   Color("color-mix(in oklab, red 30%, blue)")       # weighted
   Color("color-mix(in oklch longer hue, red, blue)")  # <Color #009300>

Any colour this package reads can go in one, including another
``color-mix()``, and more than two are allowed.

Percentages follow CSS, which means shares adding up to less than 100% leave
the rest as transparency. So these two are the same colour and differ only in
being opaque:

.. code-block:: python

   from colourings import Color

   Color("color-mix(in lch, purple 30%, plum 30%)").alpha  # 0.6
   Color("color-mix(in lch, purple 80%, plum 80%)").alpha  # 1.0

Interpolation premultiplies by alpha, as CSS specifies, which is why mixing
with ``transparent`` **fades** a colour instead of darkening it.
``transparent`` is a transparent *black*, and interpolating unweighted
channels would drag towards it:

.. code-block:: python

   from colourings import Color

   Color("color-mix(in oklab, red, transparent)")        # <Color red>
   Color("color-mix(in oklab, red, transparent)").alpha  # 0.5

Mixing works ``in hsl``, ``lab``, ``lch``, ``oklab`` and ``oklch``, with
``shorter hue`` or ``longer hue``. CSS also allows ``srgb``, ``srgb-linear``,
``hwb``, ``xyz`` and the predefined RGB spaces, and the ``increasing`` and
``decreasing`` hue methods; those raise rather than being quietly substituted.

.. note::

   ``lab`` and ``lch`` here are D65 where CSS defines them against D50, which
   is the difference the conversions already carry. See :doc:`spaces`.

``color()`` and the predefined spaces
-------------------------------------

.. code-block:: python

   from colourings import Color

   Color("color(srgb 0.2 0.5 0.7)")        # <Color #337fb2>
   Color("color(display-p3 0.4 0.5 0.6)")  # <Color #5f809c>
   Color("color(rec2020 0.3 0.5 0.6)")     # <Color #007d97>
   Color("color(xyz 0.9504559270516716 1 1.0890577507598784)")  # <Color white>
   Color("color(srgb 1 0 0 / 50%)").alpha  # 0.5

Read: ``srgb``, ``srgb-linear``, ``display-p3``, ``a98-rgb``, ``rec2020``,
``xyz`` and ``xyz-d65``. Components may be numbers or percentages, with
``100%`` meaning 1 in all of them, and values outside ``[0, 1]`` are allowed as
CSS allows them.

A wide-gamut colour is converted, and clipped if it does not fit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These spaces reach colours sRGB cannot show, and a ``Color`` holds sRGB. A
value that fits converts exactly; one that does not lands on the edge -- the
same rule as every other out-of-gamut input. **Ask before trusting one:**

.. code-block:: python

   from colourings import in_srgb_gamut

   in_srgb_gamut((0.4, 0.5, 0.6), "display-p3")  # True, converts exactly
   in_srgb_gamut((0.2, 0.5, 0.7), "display-p3")  # False, its red is -0.083
   in_srgb_gamut((1, 0, 0), "rec2020")           # False, far outside

The second is worth a look: it seems a modest colour and is outside sRGB. See
:doc:`ranges`.

What is not read
^^^^^^^^^^^^^^^^

``prophoto-rgb`` and ``xyz-d50`` raise, naming themselves:

.. code-block:: python

   from colourings import Color, InvalidColorError

   try:
       Color("color(prophoto-rgb 0.4 0.5 0.6)")
   except InvalidColorError as e:
       print(e)
   # color() cannot read 'prophoto-rgb' yet. This package converts a98-rgb, display-p3, rec2020, srgb, srgb-linear, xyz, xyz-d65.

Both are relative to D50, and reading them needs a chromatic adaptation this
library does not have. Naming them is deliberate: they are real spaces that
are simply not implemented, which is a different answer from "not a colour".

Testing a string first
----------------------

``colourings.css`` holds the parser, if you want to check a string before
building from it:

.. code-block:: python

   from colourings.css import is_css

   is_css("rgb(255 0 0)")   # True
   is_css("color(srgb 1 0 0)")  # True
   is_css("rebeccapurple")  # False, a name rather than a function