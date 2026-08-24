from pypdf import PdfReader

from pdf_extractor.engine import extract_pages, read_pdf_metadata


def test_read_pdf_metadata_valid(ten_page_pdf):
    result = read_pdf_metadata(ten_page_pdf)
    assert result.ok
    assert result.value.total_pages == 10
    assert result.value.is_encrypted is False


def test_read_pdf_metadata_encrypted(encrypted_pdf):
    result = read_pdf_metadata(encrypted_pdf)
    assert not result.ok
    assert result.errors[0].reason == "ENCRYPTED"


def test_read_pdf_metadata_corrupt(corrupt_pdf):
    result = read_pdf_metadata(corrupt_pdf)
    assert not result.ok
    assert result.errors[0].reason == "CORRUPT_FILE"


def test_read_pdf_metadata_missing(missing_pdf):
    result = read_pdf_metadata(missing_pdf)
    assert not result.ok
    assert result.errors[0].reason == "FILE_NOT_FOUND"


def test_extract_pages_writes_correct_order(ten_page_pdf, tmp_path):
    dest = tmp_path / "out.pdf"
    page_indices = [0, 5, 1, 6]
    result = extract_pages(ten_page_pdf, page_indices, str(dest))
    assert result.ok
    reader = PdfReader(str(dest))
    assert len(reader.pages) == len(page_indices)


def test_extract_pages_empty_selection(ten_page_pdf, tmp_path):
    dest = tmp_path / "out.pdf"
    result = extract_pages(ten_page_pdf, [], str(dest))
    assert not result.ok
    assert result.errors[0].reason == "EMPTY_SELECTION"


def test_extract_pages_source_corrupt(corrupt_pdf, tmp_path):
    dest = tmp_path / "out.pdf"
    result = extract_pages(corrupt_pdf, [0], str(dest))
    assert not result.ok
    assert result.errors[0].reason == "SOURCE_UNREADABLE"


def test_extract_pages_progress_callback(ten_page_pdf, tmp_path):
    dest = tmp_path / "out.pdf"
    calls = []
    result = extract_pages(
        ten_page_pdf, [0, 1, 2, 3, 4], str(dest), progress_cb=lambda c, t: calls.append((c, t))
    )
    assert result.ok
    assert calls
    assert all(t == 5 for _, t in calls)
    currents = [c for c, _ in calls]
    assert currents == sorted(currents)
    assert currents[-1] == 5
