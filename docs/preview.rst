Previewing a colour
===================

In a notebook
-------------

A ``Color`` displays as a swatch -- no toolkit, nothing to close:

.. code-block:: python

   from colourings import Color

   # Each of these renders as a coloured square with its name. A translucent
   # one is drawn over a checkerboard, so its alpha is visible.
   Color("rebeccapurple")
   Color("red", alpha=0.5)

This is ``_repr_html_``, so it works in Jupyter, IPython, Marimo and anything
else that asks an object for HTML. It needs nothing beyond the library.

The fragment is available directly, if you are assembling a page:

.. code-block:: python

   from colourings import Color

   Color("red")._repr_html_()[:32]  # '<div style="display:inline-flex;'

Nothing in it is escaped, because nothing in it needs escaping: the label is a
colour name or a hex string, and the rest is generated numbers.

In a window
-----------

``Color.preview()`` opens a window filled with the colour, sized in pixels:

.. code-block:: python

   from colourings import Color

   # The size is in pixels, and defaults to 200x200.
   Color("rebeccapurple").preview()
   Color("rebeccapurple").preview(400, 100)

An alpha other than ``1`` is not rendered, and warns.

Requires ``tkinter``
^^^^^^^^^^^^^^^^^^^^

This is the only part of the library that needs a GUI toolkit. ``tkinter`` is
imported inside the method rather than at module scope, so ``import
colourings`` neither pays for it -- tkinter costs roughly three times what the
rest of this package does to import, since it loads a C extension and links
Tcl/Tk -- nor fails on a machine that does not have it.

Being in the standard library does not mean it is installed. CPython ships
``tkinter`` on Windows and macOS, but most Linux distributions package it
separately, and a minimal install or a slim container image will not have it.
Calling ``preview()`` there raises ``ImportError`` naming what to install:
``python3-tkinter`` on the Red Hat family, ``python3-tk`` on Debian and
Ubuntu.

Every other part of the library works without it, and the notebook swatch
above is the alternative that always works.