import pytest
from hypothesis import settings

from colourings.conversions import clear_caches

## No per-example deadline. Conversions are memoized, so the first example of
## a test pays for every cache miss and the rest pay for none: the first can be
## an order of magnitude slower than the median, which is exactly the shape
## Hypothesis's default 200ms deadline reports as a flaky failure. The suite is
## still bounded, by the example count rather than by a stopwatch.
settings.register_profile("colourings", deadline=None)
## A deliberate deep run, for before a release or after touching a conversion:
## `pytest --hypothesis-profile=deep`. Twenty times the examples, which is
## minutes rather than seconds, so it is not what CI runs.
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
