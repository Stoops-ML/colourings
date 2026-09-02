Installation
============

Requirements
------------

Python 3.10 or newer. There are no runtime dependencies.

From PyPI
---------

.. code-block:: bash

   pip install colourings

From source
-----------

.. code-block:: bash

   git clone https://github.com/Stoops-ML/colourings.git
   cd colourings
   pip install -e .

Checking it works
-----------------

.. code-block:: python

   from colourings import Color

   Color("rebeccapurple").hex_l  # '#663399'

Optional: ``tkinter``
---------------------

Everything in the library works without a GUI toolkit except
:meth:`~colourings.colour.Color.preview`, which opens a window. ``tkinter`` is
imported inside that method rather than at module scope, so ``import
colourings`` neither pays for it nor fails without it.

Being in the standard library does not mean it is installed. CPython ships
``tkinter`` on Windows and macOS, but most Linux distributions package it
separately and a slim container image will not have it. Calling ``preview()``
there raises ``ImportError`` naming what to install: ``python3-tkinter`` on the
Red Hat family, ``python3-tk`` on Debian and Ubuntu.

See :doc:`preview` for the alternative, which needs nothing extra.