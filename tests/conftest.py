import pytest

from colourings.conversions import clear_caches


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
