"""Shared data types for the PDF engine: the Result/FieldError error convention.

Every public function in engine.py and validation.py returns a Result instead
of raising for expected failure modes (bad input, corrupt/encrypted files).
Only true programmer errors are allowed to raise.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class FieldError:
    """One structured validation or processing problem."""

    location: str       # e.g. "range[2]", "split_point", "file"
    input_value: str    # raw offending text, for display
    reason: str          # machine-readable code, e.g. "DESCENDING_RANGE"
    message: str         # human-readable message for the UI


@dataclass(frozen=True)
class Result(Generic[T]):
    ok: bool
    value: T | None = None
    errors: list[FieldError] = field(default_factory=list)

    @staticmethod
    def success(value: T) -> "Result[T]":
        return Result(ok=True, value=value, errors=[])

    @staticmethod
    def failure(errors: list[FieldError]) -> "Result[T]":
        return Result(ok=False, value=None, errors=errors)


@dataclass(frozen=True)
class PdfMeta:
    file_path: str
    total_pages: int
    is_encrypted: bool
