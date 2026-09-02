"""Exceptions raised for values that are not usable colors.

Errors about how a helper was *called* -- too many constructor arguments, a
scale with fewer than two colors -- remain plain ``ValueError`` or
``TypeError``. The classes here are for values that were meant to be a color
and are not.
"""

from __future__ import annotations


class ColorError(ValueError, TypeError):
    """Base class for every error raised about a color value.

    Inherits from both ``ValueError`` and ``TypeError`` because the helpers
    historically raised one or the other for the same kind of failure:
    ``hsl2rgb`` rejected an invalid HSL with ``ValueError`` while
    ``Color.set_hsl`` rejected the same value with ``TypeError``. Deriving
    from both lets the package report one consistent exception per kind of
    failure without invalidating any ``except`` clause written against the
    old behaviour.
    """


class InvalidColorError(ColorError):
    """A value is not valid in the color format it was given as.

    Raised for a component outside its range, a sequence of the wrong length,
    and a malformed hexadecimal or web color.
    """


class AmbiguousColorError(ColorError):
    """A value could be read as more than one color format.

    ``(0, 0, 0)`` is a valid RGB triple and a valid HSL triple, so it cannot
    be identified without being named.
    """


class UnknownColorError(ColorError):
    """A value does not match any supported color format."""
