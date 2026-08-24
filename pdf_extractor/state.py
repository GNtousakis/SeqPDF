"""Central state/orchestration class.

PDFApp holds no PDF logic itself — every mutation either updates plain
attributes or delegates to pdf_extractor.engine. This is the only module
allowed to import both engine and (eventually, from ui/*.py) be bound to
NiceGUI widgets; it must never import nicegui/pywebview itself, so it stays
testable with plain pytest.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pdf_extractor import engine
from pdf_extractor.models import FieldError

MODE_CUSTOM_SEQUENCE = "custom_sequence"
MODE_SPLIT_INTERLEAVE = "split_interleave"


@dataclass
class PDFApp:
    # file / document state
    file_path: str | None = None
    total_pages: int = 0
    is_encrypted: bool = False
    file_load_errors: list[FieldError] = field(default_factory=list)

    # mode
    mode: str = MODE_CUSTOM_SEQUENCE

    # custom sequence inputs
    custom_sequence_text: str = ""

    # split interleave inputs (1-indexed count of pages in the first half)
    split_point_input: int | None = None

    # derived / validation state
    computed_page_indices: list[int] = field(default_factory=list)
    validation_errors: list[FieldError] = field(default_factory=list)
    is_valid: bool = False

    # extraction/output state
    output_path: str | None = None
    is_extracting: bool = False
    extraction_progress: tuple[int, int] | None = None
    extraction_errors: list[FieldError] = field(default_factory=list)

    def load_file(self, path: str) -> None:
        """Reads metadata for a newly uploaded file and resets all
        mode-specific inputs and validation/extraction state."""
        result = engine.read_pdf_metadata(path)

        if result.ok:
            self.file_path = path
            self.total_pages = result.value.total_pages
            self.is_encrypted = result.value.is_encrypted
            self.file_load_errors = []
        else:
            self.file_path = None
            self.total_pages = 0
            self.is_encrypted = False
            self.file_load_errors = result.errors

        self.custom_sequence_text = ""
        self.split_point_input = None
        self.computed_page_indices = []
        self.validation_errors = []
        self.is_valid = False
        self.output_path = None
        self.is_extracting = False
        self.extraction_progress = None
        self.extraction_errors = []

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.validate()

    def update_custom_sequence_text(self, text: str) -> None:
        self.custom_sequence_text = text
        self.validate()

    def update_split_point(self, value: int | None) -> None:
        self.split_point_input = value
        self.validate()

    def validate(self) -> None:
        """Delegates to the engine function for the current mode; updates
        computed_page_indices / validation_errors / is_valid. No PDF math
        happens here — pure orchestration."""
        if not self.file_path or self.total_pages == 0:
            self.computed_page_indices = []
            self.validation_errors = []
            self.is_valid = False
            return

        if self.mode == MODE_CUSTOM_SEQUENCE:
            result = engine.parse_custom_sequence(self.custom_sequence_text, self.total_pages)
        elif self.mode == MODE_SPLIT_INTERLEAVE:
            if self.split_point_input is None:
                self.computed_page_indices = []
                self.validation_errors = []
                self.is_valid = False
                return
            result = engine.split_interleave(self.total_pages, self.split_point_input)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        if result.ok:
            self.computed_page_indices = result.value
            self.validation_errors = []
            self.is_valid = True
        else:
            self.computed_page_indices = []
            self.validation_errors = result.errors
            self.is_valid = False

    def extract(self, dest_path: str) -> None:
        """Guards on is_valid; calls engine.extract_pages, tracking
        progress via extraction_progress. Callers driving a UI should
        dispatch this off the main thread (e.g. NiceGUI's run.io_bound) —
        this method itself has no threading/UI awareness."""
        if not self.is_valid or not self.file_path:
            return

        self.is_extracting = True
        self.extraction_errors = []
        self.extraction_progress = (0, len(self.computed_page_indices))

        def _progress(current: int, total: int) -> None:
            self.extraction_progress = (current, total)

        result = engine.extract_pages(
            self.file_path, self.computed_page_indices, dest_path, progress_cb=_progress
        )

        if result.ok:
            self.output_path = result.value
        else:
            self.output_path = None
            self.extraction_errors = result.errors

        self.is_extracting = False
