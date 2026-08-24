import pytest

from pdf_extractor.engine import split_interleave


@pytest.mark.parametrize(
    "total_pages, split_point, expected",
    [
        (10, 5, [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]),
        (11, 5, [0, 5, 1, 6, 2, 7, 3, 8, 4, 9, 10]),
        (11, 6, [0, 6, 1, 7, 2, 8, 3, 9, 4, 10, 5]),
        (10, 8, [0, 8, 1, 9, 2, 3, 4, 5, 6, 7]),
        (10, 2, [0, 2, 1, 3, 4, 5, 6, 7, 8, 9]),
        (10, 1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        (10, 9, [0, 9, 1, 2, 3, 4, 5, 6, 7, 8]),
        (2, 1, [0, 1]),
    ],
)
def test_split_interleave_valid(total_pages, split_point, expected):
    result = split_interleave(total_pages, split_point)
    assert result.ok
    assert result.value == expected


@pytest.mark.parametrize(
    "total_pages, split_point, expected_reason",
    [
        (10, 0, "SPLIT_OUT_OF_RANGE"),
        (10, 10, "SPLIT_OUT_OF_RANGE"),
        (10, -1, "SPLIT_OUT_OF_RANGE"),
        (0, 0, "INVALID_TOTAL"),
    ],
)
def test_split_interleave_invalid(total_pages, split_point, expected_reason):
    result = split_interleave(total_pages, split_point)
    assert not result.ok
    assert result.errors[0].reason == expected_reason
