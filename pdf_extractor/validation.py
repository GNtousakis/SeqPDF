"""Pure validation helpers for the custom-sequence parser.

No NiceGUI/pywebview imports allowed in this module — it must be importable
and testable with plain pytest, independent of the UI framework.
"""
from __future__ import annotations

import re

from pdf_extractor.models import FieldError, Result

_RANGE_RE = re.compile(r"(\d+)-(\d+)")
_NUMBER_RE = re.compile(r"\d+")


def tokenize(raw_text: str) -> list[str]:
    """Splits on commas, strips all whitespace (including internal, e.g.
    "10 - 15" -> "10-15"), and drops empty tokens caused by trailing/extra
    commas."""
    tokens = []
    for piece in raw_text.split(","):
        cleaned = "".join(piece.split())
        if cleaned:
            tokens.append(cleaned)
    return tokens


def parse_single_token(token: str, index: int, total_pages: int) -> Result[list[int]]:
    """Parses one token (a single 1-indexed page number or an inclusive
    range like "10-15") into a list of 0-indexed page numbers."""
    location = f"token[{index}]"

    number_match = _NUMBER_RE.fullmatch(token)
    if number_match:
        page = int(token)
        if not (1 <= page <= total_pages):
            return Result.failure([
                FieldError(
                    location=location,
                    input_value=token,
                    reason="OUT_OF_RANGE",
                    message=f"Page {page} is out of range (document has {total_pages} pages).",
                )
            ])
        return Result.success([page - 1])

    range_match = _RANGE_RE.fullmatch(token)
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        if start > end:
            return Result.failure([
                FieldError(
                    location=location,
                    input_value=token,
                    reason="DESCENDING_RANGE",
                    message=f"Range {start}-{end} is descending; did you mean {end}-{start}?",
                )
            ])
        errors: list[FieldError] = []
        for bound in (start, end):
            if not (1 <= bound <= total_pages):
                errors.append(
                    FieldError(
                        location=location,
                        input_value=token,
                        reason="OUT_OF_RANGE",
                        message=f"Page {bound} is out of range (document has {total_pages} pages).",
                    )
                )
        if errors:
            return Result.failure(errors)
        return Result.success([p - 1 for p in range(start, end + 1)])

    if "-" in token and _NUMBER_RE.search(token):
        reason = "MALFORMED_RANGE"
        message = f"'{token}' is not a valid page range."
    else:
        reason = "NOT_A_NUMBER"
        message = f"'{token}' is not a valid page number."
    return Result.failure([FieldError(location=location, input_value=token, reason=reason, message=message)])


def check_duplicates(pages: list[int]) -> list[FieldError]:
    """Returns one FieldError per 0-indexed page value that appears more
    than once in the flat sequence, in first-seen order."""
    seen: set[int] = set()
    reported: set[int] = set()
    errors: list[FieldError] = []
    for page in pages:
        if page in seen and page not in reported:
            errors.append(
                FieldError(
                    location=f"page[{page + 1}]",
                    input_value=str(page + 1),
                    reason="DUPLICATE_PAGE",
                    message=f"Page {page + 1} was listed more than once.",
                )
            )
            reported.add(page)
        seen.add(page)
    return errors
