Compositing and blend modes
===========================

``over``
--------

``over`` draws this colour on another, which is what its alpha means:

.. code-block:: python

   from colourings import Color

   Color("red", alpha=0.5).over("white").rgb
   # RGB(red=255.0, green=127.5, blue=127.5)

This colour is the source and the argument is the backdrop, the same way round
as CSS. The result's alpha is ``a + b * (1 - a)``, so an opaque backdrop gives
an opaque result.

``blend``
---------

``blend`` does the same through any of CSS's sixteen blend modes.

Separable modes
^^^^^^^^^^^^^^^

Twelve are **separable** -- each channel is blended on its own: ``normal``,
``multiply``, ``screen``, ``overlay``, ``darken``, ``lighten``,
``color-dodge``, ``color-burn``, ``hard-light``, ``soft-light``,
``difference``, ``exclusion``.

.. code-block:: python

   from colourings import Color

   Color("red").blend("cyan", "multiply")  # <Color black>
   Color("red").blend("cyan", "screen")  # <Color white>
   Color("black").blend("#3d7ab8", "color-dodge")  # <Color #3d7ab8>, unchanged

Non-separable modes
^^^^^^^^^^^^^^^^^^^

Four read all three channels together, taking some of hue, saturation and luma
from each operand:

.. list-table::
   :header-rows: 1
   :widths: 25 37 38

   * - mode
     - takes from the source
     - takes from the backdrop
   * - ``hue``
     - hue
     - saturation and luma
   * - ``saturation``
     - saturation
     - hue and luma
   * - ``color``
     - hue and saturation
     - luma
   * - ``luminosity``
     - luma
     - hue and saturation

.. code-block:: python

   from colourings import Color

   # Tint a grey with a colour's hue, keeping the grey's lightness.
   Color("#3d7ab8").blend("#808080", "color")  # <Color #4e8bc9>

   # luminosity is color with the operands swapped, exactly.
   Color("red").blend("cyan", "luminosity") == Color("cyan").blend("red", "color")
   # True

.. warning::

   Their *luma* is the specification's ``Lum`` -- ``0.3R + 0.59G + 0.11B`` on
   the channels as they stand -- and **not** the WCAG relative luminance that
   :doc:`contrast` reports, which uses different coefficients on linearised
   channels. The two are not interchangeable, and only one of them is what a
   browser blends with.

Encoded or linear
-----------------

Compositing happens on the channels **as encoded**, which is what CSS, canvas
and every renderer do -- and is not the physically correct answer, because
light adds linearly and sRGB is not linear in light. The gap is not subtle:

.. code-block:: python

   from colourings import Color

   Color("red", alpha=0.5).over("white").green  # 127.5, what a browser shows
   Color("red", alpha=0.5).over("white", linear=True).green  # 187.516...

Sixty channel steps. Encoded is the default because it is what you are
comparing against; pass ``linear=True`` when you want the physical answer, and
expect no browser to agree with it.

``linear`` applies to ``blend`` as well as ``over``.

Fully transparent results
-------------------------

When both operands are fully transparent there is nothing visible, so no
colour is more right than another. The source's is kept, so the result still
says where it came from:

.. code-block:: python

   from colourings import Color

   result = Color("red", alpha=0.0).over(Color("blue", alpha=0.0))
   result.alpha  # 0.0
   result.web    # red

An unknown mode
---------------

``blend`` raises rather than quietly doing something else:

.. code-block:: python

   from colourings import Color

   try:
       Color("red").blend("cyan", "divide")
   except ValueError as e:
       print(e)
   # Unknown blend mode 'divide'. Choose one of: color, color-burn, color-dodge,
   # darken, difference, exclusion, hard-light, hue, lighten, luminosity, multiply,
   # normal, overlay, saturation, screen, soft-light.