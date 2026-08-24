import pytest

from pdf_extractor.engine import parse_custom_sequence


@pytest.mark.parametrize(
    "raw_text, total_pages, expected",
    [
        ("1,5,10-15", 20, [0, 4, 9, 10, 11, 12, 13, 14]),
        ("1, 5, 10-15", 20, [0, 4, 9, 10, 11, 12, 13, 14]),
        ("  1 ,  5  , 10 - 15 ", 20, [0, 4, 9, 10, 11, 12, 13, 14]),
        ("1,5,", 20, [0, 4]),
        ("5,1,3", 20, [4, 0, 2]),
        ("1-1", 20, [0]),
    ],
)
def test_parse_custom_sequence_valid(raw_text, total_pages, expected):
    result = parse_custom_sequence(raw_text, total_pages)
    assert result.ok, result.errors
    assert result.value == expected


@pytest.mark.parametrize(
    "raw_text, total_pages, expected_reason",
    [
        ("", 20, "EMPTY_INPUT"),
        ("0", 20, "OUT_OF_RANGE"),
        ("21", 20, "OUT_OF_RANGE"),
        ("5-3", 20, "DESCENDING_RANGE"),
        ("abc", 20, "NOT_A_NUMBER"),
        ("1.5", 20, "NOT_A_NUMBER"),
        ("1-", 20, "MALFORMED_RANGE"),
        ("-5", 20, "MALFORMED_RANGE"),
        ("1,1", 20, "DUPLICATE_PAGE"),
        ("1-3,2-4", 20, "DUPLICATE_PAGE"),
    ],
)
def test_parse_custom_sequence_invalid(raw_text, total_pages, expected_reason):
    result = parse_custom_sequence(raw_text, total_pages)
    assert not result.ok
    assert any(e.reason == expected_reason for e in result.errors)


def test_parse_custom_sequence_collects_all_errors():
    result = parse_custom_sequence("abc,5-3,25", 20)
    assert not result.ok
    reasons = {e.reason for e in result.errors}
    assert reasons == {"NOT_A_NUMBER", "DESCENDING_RANGE", "OUT_OF_RANGE"}
    assert len(result.errors) == 3
