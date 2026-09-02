Colour spaces and conversions
=============================

Perceptual spaces
-----------------

``lab``, ``lch``, ``oklab`` and ``oklch`` are perceptually uniform, so they
are the ones to interpolate or measure distance in. ``lch`` and ``oklch`` are
the polar forms, which makes them the convenient ones for adjusting lightness
or chroma without shifting hue.

.. code-block:: python

   from colourings import Color

   c = Color("rebeccapurple")
   print(c.lab)    # LAB(lightness=32.9024..., a=42.8830..., b=-47.1486...)
   print(c.lch)    # LCH(lightness=32.9024..., chroma=63.7334..., hue=312.2874...)
   print(c.oklab)  # OKLAB(lightness=0.4402..., a=0.0881..., b=-0.1338...)
   print(c.oklch)  # OKLCH(lightness=0.4402..., chroma=0.1602..., hue=303.3729...)

   lighter = Color(lch=(c.lch.lightness + 20, c.lch.chroma, c.lch.hue))

Which one to use
----------------

``oklab`` is the more uniform of the two pairs, most visibly around blue,
where CIE L*a*b* is known to bend. Reach for ``oklab`` for interpolation and
``oklch`` when you want a hue arc.

The two pairs are on different scales, which is the usual source of confusion:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * -
     - CIE L*a*b*
     - Oklab
   * - lightness
     - ``[0, 100]``
     - ``[0, 1]``
   * - chroma axes
     - ``[-128, 127]``
     - ``[-0.4, 0.4]``

The Oklab scale matches the CSS ``oklab()`` and ``oklch()`` functions, so a
value moves between this library and a stylesheet unchanged.

Illuminants
-----------

The CIE conversions use the **D65** illuminant, which is the one sRGB is
defined against. Values are not interchangeable with a library that uses D50.

Oklab is defined against D65 too, but is derived from sRGB directly rather
than through this library's XYZ: the seven-digit XYZ matrix is not precise
enough to leave a grey neutral in Oklab, and routing through it would give
every grey a faint cast.

.. note::

   CSS defines ``lab()`` and ``lch()`` against D50, where this library uses
   D65. That difference is real and is the reason ``prophoto-rgb`` and
   ``xyz-d50`` are not read at all -- see :doc:`css`.

Function-based conversions
--------------------------

Use the conversion helpers directly when you do not need the class API:

.. code-block:: python

   from colourings.conversions import hsl2web, rgb2hex, rgb2hsl, web2rgb

   print(rgb2hex((255, 0, 0)))      # #f00
   print(rgb2hsl((255, 0, 0)))      # HSL(hue=0.0, saturation=100.0, lightness=50.0)
   print(web2rgb("rebeccapurple"))  # RGB(red=102.0, green=51.0, blue=153.0)
   print(hsl2web((0, 0, 50.2)))     # gray

They are named ``<from>2<to>`` and cover conversion paths across:

* ``rgb``, ``rgba``, ``rgbf``, ``rgbaf``
* ``hsl``, ``hsla``, ``hslf``, ``hslaf``
* ``hsv``
* ``xyz``, ``lab``, ``lch`` -- CIE, D65
* ``oklab``, ``oklch``
* ``cmyk``, ``yuv``
* ``hex`` and ``web``

The full list is in :doc:`api`.

Caching
-------

Conversions are memoized with a bounded LRU cache, so repeated lookups of the
same colour are served from it. Results are immutable, so callers may share
them safely, and repeated calls return the identical object:

.. code-block:: python

   from colourings.conversions import clear_caches, rgb2hsl

   assert rgb2hsl((255, 0, 0)) is rgb2hsl((255, 0, 0))

   clear_caches()  # releases the cached results; never needed for correctness

The cache is bounded because hex and RGB inputs form a very large key space
while the palette an application actually uses is typically tiny.

Shape predicates
----------------

``colourings.identify`` holds the predicates that decide what a value is.
They are what the constructor dispatches on, and they are useful directly when
validating input:

.. code-block:: python

   from colourings.identify import is_hsl, is_rgb, is_web

   is_rgb((255, 0, 0))  # True
   is_hsl((0, 100, 50))  # True
   is_web("rebeccapurple")  # True
   is_rgb((0, 0, 0))  # True, and so is is_hsl -- which is why that is ambiguous