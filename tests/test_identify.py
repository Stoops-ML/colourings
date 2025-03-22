from colourings import Color
from colourings.identify import (
    is_hsl,
    is_hsla,
    is_hslaf,
    is_hslf,
    is_rgb,
    is_rgba,
    is_rgbaf,
    is_rgbf,
)


def test_bad_rbg():
    assert not is_rgb((300, 0, 0))
    assert not is_rgb((30, 300, 0, 0))
    assert not is_rgb("30, 300, 0, 0")
    assert not is_rgb(int)


def test_bad_rbgf():
    assert not is_rgbf((1.1, 0, 0))
    assert not is_rgbf((1.1, 2, 0, 0))
    assert not is_rgbf("30, 300, 0, 0")
    assert not is_rgbf(int)


def test_bad_rbgaf():
    assert not is_rgbaf((1.1, 0, 0))
    assert not is_rgbaf((1.1, 2, 0, 0))
    assert not is_rgbaf("30, 300, 0, 0")
    assert not is_rgbaf(int)


def test_bad_rbga():
    assert not is_rgba((255.1, 0, 0))
    assert not is_rgba((255.1, 2, 0, 0))
    assert not is_rgba("30, 300, 0, 0")
    assert not is_rgba(int)


def test_bad_hsl():
    assert not is_hsl((400, 0, 0))
    assert not is_hsl((30, 300, 0, 0))
    assert not is_hsl("30, 300, 0, 0")
    assert not is_hsl(int)


def test_bad_hsla():
    assert not is_hsla((110, 0, 0))
    assert not is_hsla((110, 200, 0, 0))
    assert not is_hsla("30, 300, 0, 0")
    assert not is_hsla(int)


def test_is_hslaf():
    assert is_hslaf((0, 0, 0, 0))
    assert is_hslaf(Color(hslaf=(0, 0, 0, 0)).hsla)
    assert not is_hslaf((2, 0, 0, 0))
    assert not is_hslaf((0, 2, 0, 0))
    assert not is_hslaf((0, 0, 2, 0))
    assert not is_hslaf((0, 0, 0, 2))
    assert not is_hslaf((-2, 0, 0, 0))
    assert not is_hslaf((0, -2, 0, 0))
    assert not is_hslaf((0, 0, -2, 0))
    assert not is_hslaf((0, 0, 0, -2))
    assert not is_hslaf("nope")
    assert not is_hslaf((0, 1, 0))


def test_is_hslf():
    assert is_hslf((0, 0, 0))
    assert is_hslf(Color(hslf=(0, 0, 0)).hslf)
    assert not is_hslf((2, 0, 0))
    assert not is_hslf((0, 2, 0))
    assert not is_hslf((0, 0, 2))
    assert not is_hslf((-2, 0, 0))
    assert not is_hslf((0, -2, 0))
    assert not is_hslf((0, 0, -2))
    assert not is_hslf("nope")
    assert not is_hslf((0, 1, 0, 0))
