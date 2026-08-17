import argparse

import pytest

from app.sniffer import positive_int


def test_positive_int_accepts_positive_value():
    assert positive_int("1") == 1
    assert positive_int("10") == 10


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "-1",
        "-100",
    ],
)
def test_positive_int_rejects_zero_and_negative_values(value):
    with pytest.raises(
        argparse.ArgumentTypeError,
        match="greater than zero",
    ):
        positive_int(value)


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "1.5",
        "",
    ],
)
def test_positive_int_rejects_non_integer_values(value):
    with pytest.raises(
        argparse.ArgumentTypeError,
        match="positive integer",
    ):
        positive_int(value)