from colourings.identify import is_hsl, is_rgb


def test_bad_rbg():
    assert not is_rgb((300, 0, 0))
    assert not is_rgb((30, 300, 0, 0))
    assert not is_rgb("30, 300, 0, 0")


def test_bad_hsl():
    assert not is_hsl((400, 0, 0))
    assert not is_hsl((30, 300, 0, 0))
    assert not is_hsl("30, 300, 0, 0")
