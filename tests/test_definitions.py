from colourings.definitions import (
    COLOR_NAME_TO_RGB,
    RGB,
    RGB_TO_COLOR_NAMES,
    linspace,
)


def test_bad_linspace():
    assert linspace(1, 10, 0) == []


def test_no_end_linspace():
    assert linspace(1, 10, 9, endpoint=False) == [float(i) for i in range(1, 10)]


def test_end_linspace():
    assert linspace(1, 10, 10) == [float(i) for i in range(1, 11)]


def test_linspace_one_num():
    assert linspace(1, 10, 1) == [1]


def test_linspace_lands_exactly_on_both_ends():
    """`start + step * (num - 1)` is not reliably `stop`.

    The overshoot is a unit in the last place, which is invisible in a colour
    channel that gets quantised to 8 bits on the way out but not in an alpha:
    ``Color.alpha`` rejects 1.0000000000000002, so an interpolated alpha has to
    land on 1.0 exactly."""
    assert linspace(0.03529411764705882, 1.0, 7)[-1] == 1.0
    for num in (2, 3, 5, 7, 9, 11, 17, 33, 100):
        for start in (0.0, 0.01568627450980392, 0.5, 1.0):
            for stop in (0.0, 0.803921568627451, 1.0):
                values = linspace(start, stop, num)
                assert values[0] == start
                assert values[-1] == stop
                assert all(0.0 <= v <= 1.0 for v in values)


def test_linspace_without_the_endpoint_stops_short():
    """`endpoint=False` excludes `stop`, so it must not be pinned to it."""
    assert linspace(0.0, 1.0, 4, endpoint=False) == [0.0, 0.25, 0.5, 0.75]


def test_color_name_to_rgb_values_are_float_rgb():
    for name, rgb in COLOR_NAME_TO_RGB.items():
        assert isinstance(rgb, RGB), name
        assert [type(v) for v in rgb] == [float, float, float], name


def test_rgb_to_color_names_keys_are_float_rgb():
    for rgb in RGB_TO_COLOR_NAMES:
        assert isinstance(rgb, RGB)
        assert [type(v) for v in rgb] == [float, float, float]


def test_tables_are_still_keyed_by_plain_tuples():
    """Integer tuples must keep working as keys, since they compare equal."""
    assert RGB_TO_COLOR_NAMES[(0, 0, 0)] == ["Black"]  # type: ignore
    assert RGB_TO_COLOR_NAMES[(0.0, 0.0, 0.0)] == ["Black"]  # type: ignore
    assert COLOR_NAME_TO_RGB["red"] == (255, 0, 0)
    assert COLOR_NAME_TO_RGB["red"] == (255.0, 0.0, 0.0)


def test_inverse_table_covers_every_name():
    assert len(COLOR_NAME_TO_RGB) == sum(
        len(names) for names in RGB_TO_COLOR_NAMES.values()
    )
