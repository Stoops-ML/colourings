Error handling
==============

One base class
--------------

Every failure caused by a value that is not a usable colour derives from
``ColorError``, so one ``except`` covers them all:

.. code-block:: python

   from colourings import Color, ColorError

   user_input = "chartruese"  # a misspelling of chartreuse

   try:
       Color(user_input)
   except ColorError as e:
       print(f"not a color: {e}")
   # not a color: Cannot identify color 'chartruese'. Did you mean 'chartreuse'?

``ColorError`` derives from both ``ValueError`` and ``TypeError``, so existing
``except ValueError`` and ``except TypeError`` clauses keep working unchanged.

The subclasses
--------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - exception
     - raised when
   * - ``InvalidColorError``
     - A value is not valid in the format it was given as
   * - ``AmbiguousColorError``
     - A value reads as more than one format, e.g. ``Color((0, 0, 0))``
   * - ``UnknownColorError``
     - A value matches no supported format, e.g. ``Color("nope")``

.. code-block:: python

   from colourings import Color, InvalidColorError, UnknownColorError

   try:
       Color(rgb=(300, 0, 0))
   except InvalidColorError as e:
       print(e)
   # Input is not an RGB type.

Errors about how a helper was *called* -- more than one colour argument to
``Color``, a scale with fewer than two colours -- stay plain ``ValueError`` or
``TypeError``, since they are not about a colour value.

"Did you mean"
--------------

A string that is nearly a colour gets told what it is nearly:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - typed
     - said
   * - ``rde``
     - ``Did you mean 'red'?``
   * - ``gren``
     - ``Did you mean 'green', 'grey' or 'seagreen'?``
   * - ``rbg(1 2 3)``
     - ``There is no color function called 'rbg'. Did you mean 'rgb'?``
   * - ``#ff000``
     - ``A hexadecimal color takes 3, 4, 6 or 8 digits, and this has 5.``
   * - ``xyzzy``
     - nothing beyond ``Cannot identify color 'xyzzy'.``

.. code-block:: python

   from colourings import Color, UnknownColorError

   for typed in ("rde", "gren", "rbg(1 2 3)", "#ff000", "xyzzy"):
       try:
           Color(typed)
       except UnknownColorError as e:
           print(e)
   # Cannot identify color 'rde'. Did you mean 'red'?
   # Cannot identify color 'gren'. Did you mean 'green', 'grey' or 'seagreen'?
   # Cannot identify color 'rbg(1 2 3)'. There is no color function called 'rbg'. Did you mean 'rgb'?
   # Cannot identify color '#ff000'. A hexadecimal color takes 3, 4, 6 or 8 digits, and this has 5.
   # Cannot identify color 'xyzzy'.

Nothing is offered unless it is close, since a suggestion for everything would
make the ones worth reading harder to trust. At most three are given.

Suggestions come from ``difflib`` in the standard library -- this package has
no runtime dependencies, and this feature was not going to be the first one.

System colours
--------------

A CSS system colour is recognised and says so, rather than reading as a typo.
See :doc:`css`:

.. code-block:: python

   from colourings import Color, UnknownColorError

   try:
       Color("ButtonFace")
   except UnknownColorError as e:
       print(e)
   # 'buttonface' is a CSS system color, whose value is whatever the reader's
   # platform and theme make it, so there is no fixed color to return. Name the
   # color you mean instead.

Checking before building
------------------------

``identify_color`` returns the conversion that would be used, and raises the
same errors, if you want to validate without constructing:

.. code-block:: python

   from colourings import identify_color

   identify_color("red")  # the web2hsl conversion
   identify_color("#f00")  # the hex2hsl conversion