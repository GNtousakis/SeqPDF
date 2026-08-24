from pdf_extractor.validation import check_duplicates, tokenize


def test_tokenize_whitespace_variance():
    assert tokenize("1,5,10-15") == ["1", "5", "10-15"]
    assert tokenize("1, 5, 10-15") == ["1", "5", "10-15"]
    assert tokenize("  1 ,  5  , 10 - 15 ") == ["1", "5", "10-15"]


def test_tokenize_drops_empty_tokens():
    assert tokenize("1,5,") == ["1", "5"]
    assert tokenize("") == []
    assert tokenize(",,") == []


def test_check_duplicates_none():
    assert check_duplicates([0, 4, 2]) == []


def test_check_duplicates_reports_each_dup_page_once():
    errors = check_duplicates([0, 4, 0, 4, 4])
    reasons = {e.reason for e in errors}
    assert reasons == {"DUPLICATE_PAGE"}
    reported_pages = {e.input_value for e in errors}
    assert reported_pages == {"1", "5"}
