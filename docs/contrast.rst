Contrast and luminance
======================

``Color.relative_luminance`` is WCAG 2.x relative luminance, and
``Color.contrast_ratio`` is the ratio built from it:

.. code-block:: python

   from colourings import Color

   Color("black").contrast_ratio("white")  # 21.0
   Color("#767676").contrast_ratio("white")  # 4.5422...
   Color("white").relative_luminance  # 1.0
   Color("red").relative_luminance  # 0.2126

``contrast_ratio`` takes any supported input format, and is symmetric -- which
colour is the text and which the background does not matter.

Readability
-----------

``is_readable`` applies the WCAG thresholds, and ``best_text_color`` picks
whichever candidate contrasts most:

.. code-block:: python

   from colourings import Color

   Color("#767676").is_readable("white")  # True, 4.54 clears AA
   Color("#777777").is_readable("white")  # False, 4.48 does not
   Color("#777777").is_readable("white", size="large")  # True, large text needs 3
   Color("#777777").is_readable("white", level="AAA")  # False, AAA needs 7

   Color("navy").best_text_color()  # <Color white>
   Color("navy").best_text_color(["#eeeeee", "#333333"])  # <Color #eee>

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - level
     - size
     - minimum
   * - ``AA``
     - ``normal``
     - 4.5
   * - ``AA``
     - ``large``
     - 3
   * - ``AAA``
     - ``normal``
     - 7
   * - ``AAA``
     - ``large``
     - 4.5

Large means 18pt, or 14pt bold. The table is
``colourings.definitions.WCAG_CONTRAST_MINIMUMS``.

``is_readable`` compares against the exact ratio rather than a rounded one, so
a pair at 4.4999 fails ``AA`` even though it would display as "4.50" -- which
is where it can disagree with a tool that rounds first.

``best_text_color`` judges on contrast alone, and a tie goes to whichever
candidate came first, so their order is worth choosing. A single string is
rejected rather than being read as a sequence of one-letter colours:

.. code-block:: python

   from colourings import Color

   try:
       Color("navy").best_text_color("white")
   except ValueError as e:
       print(e)
   # `candidates` must be a sequence of colors, not the single color 'white'. Pass ['white'] to mean one.

Light or dark
-------------

.. code-block:: python

   from colourings import Color

   Color("navy").is_dark  # True
   Color("yellow").is_light  # True

The threshold is not a matter of taste: it is the luminance at which contrast
against white equals contrast against black. So ``is_dark`` is exactly "white
text reads better on this than black", and it never disagrees with
``best_text_color``.

Alpha plays no part
-------------------

A contrast ratio is between two opaque colours, and a translucent one has no
contrast of its own -- it depends on whatever shows through it. Alpha is
ignored on both sides. Composite first, then ask:

.. code-block:: python

   from colourings import Color

   Color("red", alpha=0.5).over("white").contrast_ratio("white")  # 2.4354...

See :doc:`compositing`.

.. warning::

   **``Color.luminance`` is a different quantity, and is not the one to use
   here.** It is the root mean square of the channels under BT.601's luma
   weights, taken without linearising them -- a rough model of how bright a
   colour *looks*, not of how much light it carries.

   .. code-block:: python

      from colourings import Color

      Color("#777777").luminance  # 0.4666...
      Color("#777777").relative_luminance  # 0.1844...

   It keeps its name and behaviour because that is what it has always
   returned.

Function forms
--------------

The pure-function equivalents are ``rgb2relative_luminance`` and
``contrast_ratio``, both in ``colourings.conversions``:

.. code-block:: python

   from colourings.conversions import contrast_ratio, rgb2relative_luminance

   rgb2relative_luminance((255, 255, 255))  # 1.0
   contrast_ratio((0, 0, 0), (255, 255, 255))  # 21.0