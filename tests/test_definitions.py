from colourings.definitions import linspace


def test_bad_linspace():
    assert linspace(1, 10, 0) == []


def test_no_end_linspace():
    assert linspace(1, 10, 9, endpoint=False) == [float(i) for i in range(1, 10)]


def test_end_linspace():
    assert linspace(1, 10, 10) == [float(i) for i in range(1, 11)]


def test_linspace_one_num():
    assert linspace(1, 10, 1) == [1]
