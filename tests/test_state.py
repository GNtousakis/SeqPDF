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


def test_load_file_starts_with_one_default_job(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    assert len(app.jobs) == 1
    assert app.jobs[0].name == "extract_1"
    assert app.jobs[0].computed_page_indices == []
    assert app.is_valid is False


def test_load_file_resets_prior_jobs(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_custom_sequence_text(0, "1,2,3")
    app.add_job()
    assert len(app.jobs) == 2

    app.load_file(ten_page_pdf)
    assert len(app.jobs) == 1
    assert app.jobs[0].custom_sequence_text == ""
    assert app.jobs[0].computed_page_indices == []
    assert app.is_valid is False


def test_custom_sequence_valid(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_custom_sequence_text(0, "1,5,3-4")
    assert app.jobs[0].is_valid
    assert app.jobs[0].computed_page_indices == [0, 4, 2, 3]
    assert app.jobs[0].validation_errors == []


def test_custom_sequence_invalid(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_custom_sequence_text(0, "5-3")
    assert not app.jobs[0].is_valid
    assert app.jobs[0].validation_errors[0].reason == "DESCENDING_RANGE"
    assert app.jobs[0].computed_page_indices == []


def test_split_interleave_mode(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.set_job_mode(0, MODE_SPLIT_INTERLEAVE)
    app.update_job_split_point(0, 5)
    assert app.jobs[0].is_valid
    assert app.jobs[0].computed_page_indices == [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]


def test_split_interleave_out_of_range(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.set_job_mode(0, MODE_SPLIT_INTERLEAVE)
    app.update_job_split_point(0, 0)
    assert not app.jobs[0].is_valid
    assert app.jobs[0].validation_errors[0].reason == "SPLIT_OUT_OF_RANGE"


def test_split_interleave_no_input_yet_is_not_error(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.set_job_mode(0, MODE_SPLIT_INTERLEAVE)
    assert not app.jobs[0].is_valid
    assert app.jobs[0].validation_errors == []


def test_add_job_appends_default_named_job(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.add_job()
    assert len(app.jobs) == 2
    assert app.jobs[1].name == "extract_2"
    assert app.jobs[1].mode == MODE_CUSTOM_SEQUENCE


def test_remove_job_removes_by_index(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.add_job()
    app.add_job()
    app.remove_job(0)
    assert len(app.jobs) == 2
    assert app.jobs[0].name == "extract_2"


def test_remove_job_refuses_to_empty_the_list(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.remove_job(0)
    assert len(app.jobs) == 1


def test_is_valid_requires_every_job_valid(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_custom_sequence_text(0, "1,2,3")
    app.add_job()
    app.update_job_name(1, "second")
    assert not app.is_valid  # job 1 has no sequence input yet

    app.update_job_custom_sequence_text(1, "4,5")
    assert app.is_valid


def test_is_valid_requires_unique_names(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_custom_sequence_text(0, "1,2,3")
    app.add_job()
    app.update_job_custom_sequence_text(1, "4,5")
    app.update_job_name(1, app.jobs[0].name)  # duplicate of job 0's name

    assert not app.is_valid
    assert any(e.reason == "DUPLICATE_NAME" for e in app.job_name_errors(1))


def test_job_name_errors_rejects_empty_and_invalid_chars(ten_page_pdf):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_name(0, "")
    assert any(e.reason == "EMPTY_NAME" for e in app.job_name_errors(0))

    app.update_job_name(0, "bad/name")
    assert any(e.reason == "INVALID_NAME" for e in app.job_name_errors(0))


def test_extract_all_writes_one_file_per_job(ten_page_pdf, tmp_path):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_name(0, "first")
    app.update_job_custom_sequence_text(0, "1,2,3")
    app.add_job()
    app.update_job_name(1, "second")
    app.update_job_custom_sequence_text(1, "4,5")

    app.extract_all(str(tmp_path))

    assert sorted(app.output_paths) == sorted(
        [str(tmp_path / "first.pdf"), str(tmp_path / "second.pdf")]
    )
    assert (tmp_path / "first.pdf").exists()
    assert (tmp_path / "second.pdf").exists()
    assert app.extraction_errors == []
    assert app.is_extracting is False
    assert app.extraction_job_progress == (2, 2)


def test_extract_all_guards_on_invalid_state(ten_page_pdf, tmp_path):
    app = PDFApp()
    app.load_file(ten_page_pdf)
    app.update_job_custom_sequence_text(0, "5-3")  # invalid
    app.extract_all(str(tmp_path))
    assert app.output_paths == []
    assert not (tmp_path / f"{app.jobs[0].name}.pdf").exists()
