Value ranges and the sRGB gamut
===============================

Ranges
------

The library uses explicit numeric ranges per format, rather than mixing
``0..1`` and ``0..255`` conventions:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - format
     - range
   * - ``rgb``, ``rgba``
     - channels in ``[0, 255]``, alpha included
   * - ``rgbf``, ``rgbaf``
     - channels in ``[0, 1]``
   * - ``hsl``
     - ``hue`` in ``[0, 360]``, ``saturation`` and ``lightness`` in ``[0, 100]``
   * - ``hsla``
     - as ``hsl``, with alpha in ``[0, 100]``
   * - ``hslf``, ``hslaf``
     - channels in ``[0, 1]``
   * - ``hsv``
     - ``hue`` in ``[0, 360]``, ``saturation`` and ``value`` in ``[0, 100]``
   * - ``xyz``
     - CIE XYZ under D65, scaled so white has ``y`` of 100
   * - ``lab``
     - lightness in ``[0, 100]``, ``a`` and ``b`` in ``[-128, 127]``
   * - ``lch``
     - chroma in ``[0, 182]``, hue in ``[0, 360]``
   * - ``oklab``
     - lightness in ``[0, 1]``, ``a`` and ``b`` in ``[-0.4, 0.4]``
   * - ``oklch``
     - chroma in ``[0, 0.4]``, hue in ``[0, 360]``
   * - ``cmyk``
     - channels in ``[0, 100]``
   * - ``yuv``
     - BT.601, luma in ``[0, 1]``, ``u`` in ``[-0.436, 0.436]``, ``v`` in ``[-0.615, 0.615]``
   * - ``Color.alpha``
     - always ``[0, 1]``

Ranges are not the gamut
------------------------

Those ranges say what a format *accepts*, not what sRGB can *show*. ``lab``,
``lch``, ``oklab``, ``oklch``, ``xyz`` and ``yuv`` can each name a colour
outside sRGB, and a ``Color`` holds sRGB -- so such a value is **clipped** on
the way in. Quietly, and often: 88% of the ``lab`` triples in the range above
do not survive.

.. code-block:: python

   from colourings import Color

   Color(lab=(100, 120, -120)).lab
   # LAB(lightness=95.85895978712477, a=8.621537162382786, b=-6.079793114528798)
   # -- not the colour that went in

A clipped colour is indistinguishable afterwards from one that was always in
gamut, because what it stores *is* the clipped value. There is no flag to
check and nothing to recover. So ask before building it.

``in_srgb_gamut``
-----------------

.. code-block:: python

   from colourings import in_srgb_gamut

   in_srgb_gamut((53.2408, 80.0925, 67.2032), "lab")  # True, this is red
   in_srgb_gamut((100, 120, -120), "lab")             # False, would be clipped

``tolerance`` is measured in 8-bit levels and defaults to half a level, so the
default answers "would clipping change the colour as rendered". Pass
``tolerance=0`` to test the gamut exactly:

.. code-block:: python

   from colourings import in_srgb_gamut

   ## Red, written to four decimal places, sits just outside.
   in_srgb_gamut((53.2408, 80.0925, 67.2032), "lab", tolerance=0)  # False

The boundary is sharp, and every fully saturated colour sits exactly on it, so
a primary written to few enough decimal places really does fall outside and is
reported as such. That is the reason for the default rather than a flaw in it.

Which formats it answers for
----------------------------

Every other format -- ``rgb``, ``hsl``, ``hsv``, ``cmyk``, ``hex``, ``web``
and their variants -- is bounded by its own ranges, so it is representable by
construction and converts exactly. ``in_srgb_gamut`` raises ``ValueError`` if
asked about one, rather than returning a ``True`` that means nothing:

.. code-block:: python

   from colourings import in_srgb_gamut

   try:
       in_srgb_gamut((255, 0, 0), "rgb")
   except ValueError as e:
       print(e)
   # Cannot ask about the gamut of 'rgb'. Choose one of: a98-rgb, display-p3, lab,
   # lch, oklab, oklch, rec2020, xyz, xyz-d65, yuv. Every other format is bounded
   # by its own ranges, so it is always representable.

It also answers for the wide-gamut spaces that CSS ``color()`` reads --
``display-p3``, ``a98-rgb``, ``rec2020`` and ``xyz-d65``. See
:doc:`css`.

.. code-block:: python

   from colourings import in_srgb_gamut

   in_srgb_gamut((0.4, 0.5, 0.6), "display-p3")  # True, converts exactly
   in_srgb_gamut((0.2, 0.5, 0.7), "display-p3")  # False, its red is -0.083
   in_srgb_gamut((1, 0, 0), "rec2020")           # False, far outside

The second is worth a look. It seems a modest colour and it is outside sRGB. A
finished ``Color`` cannot answer this, because by then the clipping has already
happened -- which is why the question is asked of the components rather than of
a colour.

Where clipping else happens
---------------------------

Clipping is the library's consistent answer to a colour it cannot represent,
so it also applies to:

* a straight line between two saturated colours in a :doc:`gradient
  <gradients>`, which can leave the gamut in the middle;
* a wide-gamut ``color()`` value in :doc:`css`;
* a :doc:`compositing <compositing>` result driven out of range.

Reading out of range is the exception: CSS syntax **refuses** an out-of-range
component rather than clamping it, because there the number was written down
rather than computed. See :doc:`css`.