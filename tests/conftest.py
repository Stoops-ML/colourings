import sys
import types

import pytest
from hypothesis import settings

from colourings.conversions import clear_caches

## `preview()` is the one thing here that needs a GUI toolkit, and two of the
## interpreter builds CI runs on ship without one -- Ubuntu 3.12 has no
## `tkinter` at all, macOS 3.14 no `_tkinter` behind it. The preview tests
## mock `Tk` regardless, so what they need is a name to patch rather than a
## working toolkit; without this they fail for a reason that is not about this
## package, and take the coverage gate down with them.
##
## The genuinely-missing path stays covered: `test_preview_without_tkinter`
## puts None in `sys.modules` and asserts the ImportError names the package.
try:  # pragma: no cover - depends on the interpreter build, not on a branch
    import tkinter  # noqa: F401
except ImportError:  # pragma: no cover - ditto

    class _TkinterStub(types.ModuleType):
        """Enough of ``tkinter`` for ``patch("tkinter.Tk")`` to find a name."""

        Tk = types.SimpleNamespace

    sys.modules["tkinter"] = _TkinterStub("tkinter")

## No deadline. Conversions are memoized, so the first example pays for every
## cache miss and can be an order of magnitude slower than the median -- the
## shape Hypothesis's 200ms default reports as flaky. The example count still
## bounds the suite.
settings.register_profile("colourings", deadline=None)
## `pytest --hypothesis-profile=deep`, for before a release or after touching
## a conversion. Twenty times the examples, so minutes rather than seconds.
settings.register_profile("deep", deadline=None, max_examples=2000)
settings.load_profile("colourings")


@pytest.fixture(autouse=True)
def _clear_conversion_caches():
    """Give every test an empty conversion cache.

    Conversions are memoized, so without this a value computed by an earlier
    test is returned again instead of being recomputed. That matters for tests
    that patch internals to reach a specific branch: the patch would never be
    exercised if the result were already cached.
    """
    clear_caches()
    yield
    clear_caches()
