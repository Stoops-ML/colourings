import pytest
from hypothesis import settings

from colourings.conversions import clear_caches

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
