from colourings.identify import is_hsl, is_hsla, is_rgb, is_rgba


def test_bad_rbg():
    assert not is_rgb((300, 0, 0))
    assert not is_rgb((30, 300, 0, 0))
    assert not is_rgb("30, 300, 0, 0")
    assert not is_rgb(int)


def test_bad_rbga():
    assert not is_rgba((1.1, 0, 0))
    assert not is_rgba((1.1, 2, 0, 0))
    assert not is_rgba("30, 300, 0, 0")
    assert not is_rgba(int)


def test_bad_hsl():
    assert not is_hsl((400, 0, 0))
    assert not is_hsl((30, 300, 0, 0))
    assert not is_hsl("30, 300, 0, 0")
    assert not is_hsl(int)


def test_bad_hsla():
    assert not is_hsla((1.1, 0, 0))
    assert not is_hsla((1.1, 2, 0, 0))
    assert not is_hsla("30, 300, 0, 0")
    assert not is_hsla(int)
