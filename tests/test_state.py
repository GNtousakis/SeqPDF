from pdf_extractor.state import MODE_CUSTOM_SEQUENCE, MODE_SPLIT_INTERLEAVE, PDFApp


def test_load_file_valid(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    assert app.file_path == ten_page_pdf
    assert app.total_pages == 10
    assert app.is_encrypted is False
    assert app.file_load_errors == []


def test_load_file_corrupt(corrupt_pdf):
    app = PDFApp()
    app.load_file(corrupt_pdf)
    assert app.file_path is None
    assert app.total_pages == 0
    assert app.file_load_errors[0].reason == "CORRUPT_FILE"


def test_load_file_resets_prior_state(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_custom_sequence_text("1,2,3")
    assert app.is_valid

    app.load_file(ten_page_pdf)
    assert app.custom_sequence_text == ""
    assert app.computed_page_indices == []
    assert app.is_valid is False


def test_custom_sequence_valid(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_custom_sequence_text("1,5,3-4")
    assert app.is_valid
    assert app.computed_page_indices == [0, 4, 2, 3]
    assert app.validation_errors == []


def test_custom_sequence_invalid(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_custom_sequence_text("5-3")
    assert not app.is_valid
    assert app.validation_errors[0].reason == "DESCENDING_RANGE"
    assert app.computed_page_indices == []


def test_split_interleave_mode(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.set_mode(MODE_SPLIT_INTERLEAVE)
    app.update_split_point(5)
    assert app.is_valid
    assert app.computed_page_indices == [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]


def test_split_interleave_out_of_range(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.set_mode(MODE_SPLIT_INTERLEAVE)
    app.update_split_point(0)
    assert not app.is_valid
    assert app.validation_errors[0].reason == "SPLIT_OUT_OF_RANGE"


def test_split_interleave_no_input_yet_is_not_error(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.set_mode(MODE_SPLIT_INTERLEAVE)
    assert not app.is_valid
    assert app.validation_errors == []


def test_extract_writes_output(ten_page_pdf, tmp_path):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_custom_sequence_text("1,2,3")
    dest = tmp_path / "out.pdf"
    app.extract(str(dest))
    assert app.output_path == str(dest)
    assert app.extraction_errors == []
    assert app.is_extracting is False
    assert app.extraction_progress == (3, 3)


def test_extract_guards_on_invalid_state(ten_page_pdf, tmp_path):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_custom_sequence_text("5-3")  # invalid
    dest = tmp_path / "out.pdf"
    app.extract(str(dest))
    assert app.output_path is None
    assert not dest.exists()
