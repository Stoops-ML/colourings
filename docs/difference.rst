Colour difference
=================

How far apart two colours are, and what to call one:

.. code-block:: python

   from colourings import Color

   Color("black").delta_e("white")  # 100.0
   Color("#ff0000").delta_e("#ff0001")  # 0.098..., invisible
   Color("#123456").nearest_name()  # 'midnightblue'

The four metrics
----------------

In the order they were standardised:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - metric
     - what it is
   * - ``cie76``
     - Euclidean distance in CIE L*a*b*. Fast, and overstates blues badly
   * - ``cie94``
     - Weights lightness, chroma and hue separately. Not symmetric -- see below
   * - ``ciede2000``
     - What "delta E" means unqualified. The default
   * - ``ok``
     - Euclidean distance in Oklab. Perceptual and cheap, on its own scale

.. code-block:: python

   from colourings import Color

   Color("red").delta_e("blue")  # 52.881...
   Color("red").delta_e("blue", metric="cie76")  # 176.31...
   Color("red").delta_e("blue", metric="ok")  # 0.5370...

Roughly, on the three L*a*b* metrics: 1 is the smallest difference a good eye
can see side by side, 2 to 3 is noticeable, above 5 they read as different
colours. ``ok`` numbers are much smaller -- Oklab's axes run to about 0.4, not
100 -- so a threshold does not carry across.

Why the later metrics exist
---------------------------

The blue case is worth seeing:

.. code-block:: python

   from colourings.difference import delta_e_cie76, delta_e_ciede2000

   blue1, blue2 = (32.0, 79.0, -104.0), (32.0, 69.0, -100.0)
   delta_e_cie76(blue1, blue2)  # 10.77...
   delta_e_ciede2000(blue1, blue2)  # 2.7696...

Four times the distance, for a pair that looks nearly identical. CIE76 treats
L*a*b* as if it were uniform everywhere, and around blue it is not.

``cie94`` is asymmetric, by a lot
---------------------------------

.. warning::

   ``cie94`` is asymmetric by construction, and by a lot rather than a little.
   Its chroma and hue terms are divided by weights that grow with the *first*
   argument's chroma, so a dull reference down-weights nothing and reports the
   larger distance:

   .. code-block:: python

      from colourings import Color

      grey, magenta = Color("#808080"), Color("#ff00ff")
      grey.delta_e(magenta, metric="cie94")  # 115.7...
      magenta.delta_e(grey, metric="cie94")  # 19.8...

   Pass the two in the order you mean, or use ``ciede2000``, which exists
   partly because of this.

Naming a colour
---------------

.. code-block:: python

   from colourings import Color

   Color("#123456").nearest_name()  # 'midnightblue'
   Color("#ff0000").nearest_name()  # 'red'
   Color("#123456").nearest_name(metric="ciede2000")  # 'midnightblue', the same here

``nearest_name`` searches all 152 named colours and defaults to ``ok``, being
the cheap perceptual one. It returns the lowercase name; ``web`` gives the
canonical spelling for an exact match.

It always returns *something*, however far away, so check ``delta_e`` against
it before quoting it:

.. code-block:: python

   from colourings import Color

   c = Color("#123456")
   name = c.nearest_name()
   c.delta_e(name)  # 11.77..., far enough that the name is a stretch

On ``ciede2000``
----------------

.. note::

   Its constants were written from the formula rather than copied from a
   reference implementation, so they are checked against the published
   Sharma--Wu--Dalal supplementary test data -- all 34 pairs, to the four
   decimals that table gives.

   That check is worth more than it sounds. The properties this function is
   otherwise tested against -- exactly 0 against itself, exactly 100 for black
   against white, symmetry, and the neutral lightness reduction -- all still
   pass with the hue-rotation peak moved from 275° to 257°, or with a
   weighting constant mistyped. The published pairs catch every one of those.

Function forms
--------------

``colourings.difference`` holds the metrics directly. They take Lab
sequences, except ``delta_e_ok`` which takes Oklab:

.. code-block:: python

   from colourings.difference import (
       delta_e_cie76,
       delta_e_cie94,
       delta_e_ciede2000,
       delta_e_ok,
   )

   delta_e_cie76((100.0, 0.0, 0.0), (0.0, 0.0, 0.0))  # 100.0
   delta_e_ciede2000((100.0, 0.0, 0.0), (0.0, 0.0, 0.0))  # 100.0

Taking Lab directly rather than a ``Color`` matters when a value is outside
the sRGB gamut: building a ``Color`` from it would clip the input and measure
a different pair. See :doc:`ranges`.