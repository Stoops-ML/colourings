API reference
=============

The public surface
------------------

These are the top-level exports:

.. code-block:: python

   from colourings import (
       AmbiguousColorError,
       Color,
       ColorError,
       Colour,
       HSL_equivalence,
       InvalidColorError,
       RGB_color_picker,
       RGB_equivalence,
       UnknownColorError,
       clear_caches,
       color_scale,
       colour_scale,
       identify_color,
       in_srgb_gamut,
       make_color_factory,
   )

The conversion functions, the shape predicates and the CSS parser stay in
their own modules. They are a much larger surface than most callers want, and
importing the package should not put eighty names within reach of a typo.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - module
     - holds
   * - ``colourings.colour``
     - the named-colour accessors ``NAMED_HSL``, ``NAMED_RGB``, ``NAMED_HEX``
   * - ``colourings.conversions``
     - conversion utilities, plus ``rgb2relative_luminance``,
       ``contrast_ratio``, ``in_srgb_gamut`` and ``clear_caches``
   * - ``colourings.css``
     - ``css2hsl``, ``css2hsla``, ``hsla2css``, ``is_css``
   * - ``colourings.difference``
     - ``delta_e_cie76``, ``delta_e_cie94``, ``delta_e_ciede2000``,
       ``delta_e_ok``, ``hsl_difference``, ``nearest_named_hsl``
   * - ``colourings.definitions``
     - the tuple types, the matrices and the WCAG constants
   * - ``colourings.identify``
     - type and shape predicates like ``is_rgb``, ``is_hsl``, ``is_web``
   * - ``colourings.errors``
     - the exception hierarchy

Top-level package
-----------------

.. Exceptions are excluded here and documented under `Errors` below. Autodoc
   registers a re-export under both names, and a bare ``InvalidColorError`` in
   a ``Raises`` section then has two targets to choose between.

.. automodule:: colourings
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: AmbiguousColorError, ColorError, InvalidColorError,
                     UnknownColorError

Core colour model
-----------------

.. automodule:: colourings.colour
   :members:
   :undoc-members:
   :show-inheritance:

Conversions
-----------

.. automodule:: colourings.conversions
   :members:
   :undoc-members:
   :show-inheritance:

CSS syntax
----------

.. automodule:: colourings.css
   :members:
   :undoc-members:
   :show-inheritance:

Colour difference
-----------------

.. automodule:: colourings.difference
   :members:
   :undoc-members:
   :show-inheritance:

Input identification helpers
----------------------------

.. automodule:: colourings.identify
   :members:
   :undoc-members:
   :show-inheritance:

Errors
------

.. automodule:: colourings.errors
   :members:
   :undoc-members:
   :show-inheritance:

Colour definitions
------------------

.. automodule:: colourings.definitions
   :members:
   :undoc-members:
   :show-inheritance: