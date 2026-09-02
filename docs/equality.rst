Equality, hashing and picking
=============================

The default
-----------

By default, ``Color`` equality compares the RGB-equivalent rendered colour
(``hex_l``):

.. code-block:: python

   from colourings import Color

   assert Color("red") == Color("#f00")

Comparing against anything that is not a colour is ``False`` rather than an
error, and colours are hashable, so they work in sets and as dict keys:

.. code-block:: python

   from colourings import Color

   assert Color("red") != "red"
   assert len({Color("red"), Color("#f00"), Color("blue")}) == 2
   assert {Color("red"): "warm"}[Color("#f00")] == "warm"

.. warning::

   ``Color`` is mutable, so do not mutate one while it is held in a set or
   used as a dict key.

Custom strategies
-----------------

.. code-block:: python

   from colourings import Color, HSL_equivalence

   c1 = Color("red", lightness=0, equality=HSL_equivalence)
   c2 = Color("blue", lightness=0, equality=HSL_equivalence)

   print(c1 == c2)  # False

Both are black, so the default would call them equal; ``HSL_equivalence``
keeps their hue and so tells them apart.

The strategy is a comparison policy rather than part of the colour, so
``Color(other)`` does not inherit it -- it copies the value and starts from the
default. ``copy.copy`` duplicates both:

.. code-block:: python

   import copy

   from colourings import Color, HSL_equivalence, RGB_equivalence

   c = Color("red", equality=HSL_equivalence)
   print(Color(c).equality is RGB_equivalence)  # True, the default
   print(copy.copy(c).equality is HSL_equivalence)  # True

What ``==`` costs, and ``equals``
---------------------------------

``==`` consults both operands and accepts either verdict, which keeps it
symmetric but has three consequences. None of them bite while every colour
uses the default:

* **It is not transitive across mixed strategies.** With ``a`` and ``c``
  strict and ``b`` loose, ``a == b`` and ``b == c`` can both hold while
  ``a == c`` does not -- and ``set``, ``dict``, ``in`` and ``assertEqual`` all
  assume otherwise.
* **A strict strategy only holds where both colours carry it**, since the
  looser one need only agree once to satisfy the ``or``.
* **A strategy looser than ``hex_l`` breaks the hash contract**, so ``b in
  {a}`` can be ``False`` where ``a == b``. A *stricter* one is fine:
  ``HSL_equivalence`` lets two colours share a hash while comparing unequal,
  which is an ordinary collision that ``set`` resolves by comparing.

``equals`` has none of these. It takes the strategy as an argument rather than
from the operands, so it is reflexive, symmetric and transitive whenever that
strategy is -- and both built-ins are:

.. code-block:: python

   from colourings import Color, HSL_equivalence

   Color("red").equals("#f00")  # True, by hex_l
   Color("red").equals("#f00", HSL_equivalence)  # True, by HSL

Use ``equals`` where the answer matters and ``==`` where the default is fine.

Deterministic colour picking
----------------------------

Use ``pick_for`` to map arbitrary Python objects to colours:

.. code-block:: python

   from colourings import Color

   print(Color(pick_for="user:123") == Color(pick_for="user:123"))  # True
   print(Color(pick_for="user:123") == Color(pick_for="user:456"))  # False

The same value gives the same colour in **every process**, so a colour picked
for a user, a host or a branch survives a restart:

.. code-block:: python

   from colourings import Color

   print(Color(pick_for="user:123").hex_l)  # #1b1069, every run

.. warning::

   The one exception is an object relying on the default ``__repr__``, whose
   string form contains its address -- that changes every run and between
   instances, and no key function can recover from it. Give such a class a
   ``__str__``, or pass a ``pick_key`` that reads the fields you care about.

Overriding the strategy
^^^^^^^^^^^^^^^^^^^^^^^

``picker``
   A callable that returns a colour-like value.

``pick_key``
   A callable that maps objects to comparable keys.

.. code-block:: python

   from colourings import Color

   Color(pick_for=[1, 2], pick_key=lambda obj: str(sorted(obj))).hex_l  # '#ba6b12'

``hash_or_str`` was the default before 2.0 and is still available, for keys
that should hold within one process and be discarded with it:

.. code-block:: python

   from colourings.colour import Color, hash_or_str

   a = Color(pick_for="user:123", pick_key=hash_or_str)
   b = Color(pick_for="user:123", pick_key=hash_or_str)
   a == b  # True, within this process

It runs hashable objects through ``hash()``, which Python salts per process.
Because the key it builds contains the type name, and string hashing is what
gets salted, *every* hashable object came out a different colour each run while
every unhashable one was stable. Which of those you got depended on nothing
you would think to care about, so it is no longer the default.

Colour factories
----------------

``make_color_factory`` fixes constructor defaults, so a codebase can settle on
a strategy once:

.. code-block:: python

   from colourings import HSL_equivalence, make_color_factory

   StrictColor = make_color_factory(equality=HSL_equivalence)

   c = StrictColor("red")
   c.equality is HSL_equivalence  # True