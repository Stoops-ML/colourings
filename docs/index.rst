colourings
==========

A lightweight Python library for creating, converting, comparing and
interpolating colours. No runtime dependencies, typed throughout, and every
published constant traceable to a citable source.

.. code-block:: python

   from colourings import Color

   c = Color("#3d7ab8")
   c.oklch                    # OKLCH(lightness=0.5677..., chroma=0.1153..., hue=250.8861...)
   c.mix("white", 0.3).hex_l  # '#78a2cf'
   c.contrast_ratio("white")  # 4.4925..., just short of WCAG AA
   c.best_text_color()        # <Color black>

Where to start
--------------

:doc:`installation` and then :doc:`quickstart` for the tour. After that the
pages below stand on their own, in roughly the order most people need them.

If you are choosing a colour space to work in, read :doc:`ranges` first. It
explains the one thing about this library that surprises people: a ``Color``
holds sRGB, so a value from a wider space is **clipped** on the way in, and
afterwards it is indistinguishable from one that always fitted.

.. toctree::
   :maxdepth: 2
   :caption: Using colourings

   installation
   quickstart
   colors
   ranges
   spaces
   gradients
   adjusting
   css
   contrast
   difference
   compositing
   equality
   errors
   preview

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api
   changelog

A note on correctness
---------------------

Most of this library is arithmetic on published constants, and a wrong
constant there does not raise -- it returns a plausible colour that is simply
wrong. So the constants are either quoted from a citable source or derived in
exact arithmetic, and the derivations are checked against the source:

* The CIE matrices are derived rather than quoted where the published rounding
  costs accuracy, and quoted where it does not. Both choices are recorded, with
  the error each avoids, in ``colourings.definitions``.
* CIEDE2000 is checked against all 34 pairs of the published
  Sharma--Wu--Dalal supplementary test data. See :doc:`difference`.
* The wide-gamut matrices for CSS ``color()`` are each derived twice, from the
  specification's rationals and from the space's published chromaticities.
* Anything whose constants could not be confirmed raises instead of guessing.
  ``prophoto-rgb`` and ``xyz-d50`` are the current examples.

The examples on every page of this documentation are executed by the test
suite, and the values they claim are checked against what actually runs.

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`