import pytest
from pypdf import PdfWriter


def _make_pdf(path, num_pages):
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=200, height=200)
    with open(path, "wb") as f:
        writer.write(f)
    return str(path)


@pytest.fixture
def ten_page_pdf(tmp_path):
    return _make_pdf(tmp_path / "ten_pages.pdf", 10)


@pytest.fixture
def encrypted_pdf(tmp_path):
    path = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=200, height=200)
    writer.encrypt(user_password="secret", owner_password="secret-owner")
    with open(path, "wb") as f:
        writer.write(f)
    return str(path)


@pytest.fixture
def corrupt_pdf(tmp_path):
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"not a real pdf file")
    return str(path)


@pytest.fixture
def missing_pdf(tmp_path):
    return str(tmp_path / "does_not_exist.pdf")
