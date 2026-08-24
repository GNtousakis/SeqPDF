"""Pure PDF engine: sequence math + PDF I/O.

No NiceGUI/pywebview imports allowed anywhere in this module. Every public
function returns a Result (see models.py) instead of raising for expected
failure modes (bad input, corrupt/encrypted files, write failures). This is
what lets the UI layer bind directly to error state without try/except
sprinkled through event handlers.
"""
from __future__ import annotations

from typing import Callable

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from pdf_extractor.models import FieldError, PdfMeta, Result
from pdf_extractor.validation import check_duplicates, parse_single_token, tokenize


def parse_custom_sequence(raw_text: str, total_pages: int) -> Result[list[int]]:
    """Parses a print-style page string, e.g. "1, 5, 10-15", into 0-indexed
    page numbers in the order the user specified. Does not deduplicate or
    reorder: a duplicate page reference is rejected as a structured error
    (likely a typo) rather than silently collapsed, since pypdf would
    otherwise happily produce an output PDF with a repeated page and no
    indication the user's input didn't mean that.
    """
    tokens = tokenize(raw_text)
    if not tokens:
        return Result.failure([
            FieldError(
                location="input",
                input_value=raw_text,
                reason="EMPTY_INPUT",
                message="Enter at least one page or range, e.g. \"1, 5, 10-15\".",
            )
        ])

    all_errors: list[FieldError] = []
    pages: list[int] = []
    for index, token in enumerate(tokens):
        result = parse_single_token(token, index, total_pages)
        if result.ok:
            pages.extend(result.value)
        else:
            all_errors.extend(result.errors)

    if all_errors:
        return Result.failure(all_errors)

    dup_errors = check_duplicates(pages)
    if dup_errors:
        return Result.failure(dup_errors)

    return Result.success(pages)


def split_interleave(total_pages: int, split_point: int) -> Result[list[int]]:
    """Returns 0-indexed page order interleaving the first `split_point`
    pages with the remaining pages.

    Policy: zip the two halves 1:1 while both have pages remaining, then
    append whichever half is longer's leftover pages, in original order, at
    the end. No padding, no truncation, no data loss.

    `split_point` is the count of pages in the first half (equivalently,
    "split after page N" as a 1-indexed count) — callers pass it directly
    without an index translation.
    """
    errors: list[FieldError] = []
    if total_pages <= 0:
        errors.append(
            FieldError("total_pages", str(total_pages), "INVALID_TOTAL", "Document has no pages.")
        )
    if errors:
        return Result.failure(errors)

    if not (0 < split_point < total_pages):
        errors.append(
            FieldError(
                "split_point",
                str(split_point),
                "SPLIT_OUT_OF_RANGE",
                f"Split point must be between 1 and {total_pages - 1}.",
            )
        )
        return Result.failure(errors)

    first_half = list(range(0, split_point))
    second_half = list(range(split_point, total_pages))

    result: list[int] = []
    i = 0
    while i < len(first_half) and i < len(second_half):
        result.append(first_half[i])
        result.append(second_half[i])
        i += 1
    result.extend(first_half[i:])
    result.extend(second_half[i:])
    return Result.success(result)


def _try_decrypt_empty(reader: PdfReader) -> bool:
    """Attempts empty-password decryption; returns whether the reader is
    now usable (not still encrypted)."""
    if not reader.is_encrypted:
        return True
    try:
        decrypt_result = reader.decrypt("")
    except Exception:
        decrypt_result = 0
    return bool(decrypt_result)


def read_pdf_metadata(file_path: str) -> Result[PdfMeta]:
    """Opens the PDF and returns its page count. Handles missing,
    corrupt, and encrypted files without raising."""
    try:
        reader = PdfReader(file_path)
    except FileNotFoundError:
        return Result.failure([
            FieldError("file", file_path, "FILE_NOT_FOUND", "File not found.")
        ])
    except (PdfReadError, OSError, ValueError):
        return Result.failure([
            FieldError("file", file_path, "CORRUPT_FILE", "The file is not a valid PDF or is corrupted.")
        ])

    is_encrypted = bool(reader.is_encrypted)
    if is_encrypted and not _try_decrypt_empty(reader):
        return Result.failure([
            FieldError("file", file_path, "ENCRYPTED", "This PDF is password-protected and cannot be opened.")
        ])

    try:
        total_pages = len(reader.pages)
    except Exception:
        return Result.failure([
            FieldError("file", file_path, "CORRUPT_FILE", "The file is not a valid PDF or is corrupted.")
        ])

    return Result.success(PdfMeta(file_path=file_path, total_pages=total_pages, is_encrypted=is_encrypted))


def extract_pages(
    source_path: str,
    page_indices: list[int],
    dest_path: str,
    progress_cb: Callable[[int, int], None] | None = None,
) -> Result[str]:
    """Writes a new PDF at dest_path containing page_indices (0-indexed)
    from source_path, in the given order — order is the point, since it's
    what enables interleaving. progress_cb(current, total), if given, is
    called periodically so a caller can drive a progress bar; safe to omit
    for headless/test use."""
    if not page_indices:
        return Result.failure([
            FieldError("page_indices", "", "EMPTY_SELECTION", "No pages selected for extraction.")
        ])

    try:
        reader = PdfReader(source_path)
    except FileNotFoundError:
        return Result.failure([
            FieldError("file", source_path, "SOURCE_UNREADABLE", "Source file not found.")
        ])
    except (PdfReadError, OSError, ValueError):
        return Result.failure([
            FieldError("file", source_path, "SOURCE_UNREADABLE", "Source file is not a valid PDF or is corrupted.")
        ])

    if reader.is_encrypted and not _try_decrypt_empty(reader):
        return Result.failure([
            FieldError("file", source_path, "ENCRYPTED", "Source PDF is password-protected.")
        ])

    writer = PdfWriter()
    total = len(page_indices)
    try:
        for i, page_index in enumerate(page_indices):
            writer.add_page(reader.pages[page_index])
            if progress_cb is not None and (i % 25 == 0 or i == total - 1):
                progress_cb(i + 1, total)
        with open(dest_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        return Result.failure([
            FieldError("file", dest_path, "WRITE_FAILED", f"Failed to write output PDF: {e}")
        ])

    return Result.success(dest_path)
