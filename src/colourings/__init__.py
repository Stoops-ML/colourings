from .colour import Color, Colour, color_scale, colour_scale
from .conversions import in_srgb_gamut
from .errors import (
    AmbiguousColorError,
    ColorError,
    InvalidColorError,
    UnknownColorError,
)

__all__ = [
    "AmbiguousColorError",
    "Color",
    "ColorError",
    "Colour",
    "InvalidColorError",
    "UnknownColorError",
    "color_scale",
    "colour_scale",
    "in_srgb_gamut",
]


def __getattr__(name: str) -> str:
    """Resolve ``__version__`` from the installed distribution metadata.

    The version is declared once, in ``pyproject.toml``, and read back from
    the metadata built from it rather than duplicated here.

    Doing that eagerly would cost more than the rest of the package: importing
    ``importlib.metadata`` measures 50-86ms and the first lookup another
    24-78ms, against 39-53ms for all of ``colourings``. Resolving it on first
    access instead keeps ``import colourings`` free for the callers -- nearly
    all of them -- that never read the version.

    Parameters
    ----------
    name : str
        Attribute being looked up on the package.

    Returns
    -------
    str
        The installed version, when ``name`` is ``"__version__"``.

    Raises
    ------
    AttributeError
        Raised for any other name, as normal attribute lookup would.
    importlib.metadata.PackageNotFoundError
        Raised when the package is not installed, so its metadata cannot be
        read. It subclasses ``ImportError``.
    """
    if name == "__version__":
        from importlib.metadata import version

        return version("colourings")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
