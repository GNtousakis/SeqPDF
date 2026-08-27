"""Central state/orchestration class.

PDFApp holds no PDF logic itself — every mutation either updates plain
attributes or delegates to pdf_extractor.engine. This is the only module
allowed to import both engine and (eventually, from ui/*.py) be bound to
NiceGUI widgets; it must never import nicegui/pywebview itself, so it stays
testable with plain pytest.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from pdf_extractor import engine
from pdf_extractor.models import FieldError

MODE_CUSTOM_SEQUENCE = "custom_sequence"
MODE_SPLIT_INTERLEAVE = "split_interleave"

_INVALID_NAME_CHARS = set('/\\:*?"<>|')


def _default_job_name(index: int) -> str:
    return f"extract_{index + 1}"


@dataclass
class ExportJob:
    """One page-sequence configuration destined for its own output file.

    Mirrors what used to be the single set of mode/sequence fields on
    PDFApp; a document can now have many of these, each independently
    configured and validated."""

    name: str = ""
    mode: str = MODE_CUSTOM_SEQUENCE
    custom_sequence_text: str = ""
    split_point_input: int | None = None

    # derived / validation state
    computed_page_indices: list[int] = field(default_factory=list)
    validation_errors: list[FieldError] = field(default_factory=list)
    is_valid: bool = False

    def set_mode(self, mode: str, total_pages: int) -> None:
        self.mode = mode
        self.validate(total_pages)

    def update_custom_sequence_text(self, text: str, total_pages: int) -> None:
        self.custom_sequence_text = text
        self.validate(total_pages)

    def update_split_point(self, value: int | None, total_pages: int) -> None:
        self.split_point_input = value
        self.validate(total_pages)

    def validate(self, total_pages: int) -> None:
        """Delegates to the engine function for this job's mode; updates
        computed_page_indices / validation_errors / is_valid. No PDF math
        happens here — pure orchestration."""
        if total_pages == 0:
            self.computed_page_indices = []
            self.validation_errors = []
            self.is_valid = False
            return

        if self.mode == MODE_CUSTOM_SEQUENCE:
            result = engine.parse_custom_sequence(self.custom_sequence_text, total_pages)
        elif self.mode == MODE_SPLIT_INTERLEAVE:
            if self.split_point_input is None:
                self.computed_page_indices = []
                self.validation_errors = []
                self.is_valid = False
                return
            result = engine.split_interleave(total_pages, self.split_point_input)
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

    def name_errors(self, other_names: list[str]) -> list[FieldError]:
        """Validates the output name against filesystem/uniqueness rules.
        Kept separate from validate() since a name conflict depends on
        sibling jobs, not on this job's own sequence inputs."""
        name = self.name.strip()
        if not name:
            return [FieldError("name", name, "EMPTY_NAME", "Enter a name for this export.")]
        if any(c in _INVALID_NAME_CHARS for c in name):
            return [FieldError(
                "name", name, "INVALID_NAME", 'Name cannot contain / \\ : * ? " < > |'
            )]
        if any(name.lower() == other.strip().lower() for other in other_names):
            return [FieldError(
                "name", name, "DUPLICATE_NAME", f'"{name}" is already used by another export.'
            )]
        return []


@dataclass
class PDFApp:
    # file / document state
    file_path: str | None = None
    total_pages: int = 0
    is_encrypted: bool = False
    file_load_errors: list[FieldError] = field(default_factory=list)

    # one or more export configurations, each producing its own output file
    jobs: list[ExportJob] = field(default_factory=list)

    # extraction/output state
    output_paths: list[str] = field(default_factory=list)
    is_extracting: bool = False
    extraction_current_job_name: str | None = None
    extraction_job_progress: tuple[int, int] | None = None
    extraction_progress: tuple[int, int] | None = None
    extraction_errors: list[FieldError] = field(default_factory=list)

    def load_file(self, path: str) -> None:
        """Reads metadata for a newly uploaded file and resets all
        job/validation/extraction state to a single default job."""
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

        self.jobs = [ExportJob(name=_default_job_name(0))]
        self.output_paths = []
        self.is_extracting = False
        self.extraction_current_job_name = None
        self.extraction_job_progress = None
        self.extraction_progress = None
        self.extraction_errors = []

    def add_job(self) -> None:
        self.jobs.append(ExportJob(name=_default_job_name(len(self.jobs))))

    def remove_job(self, index: int) -> None:
        """No-ops if this would leave zero jobs — at least one export
        configuration must always exist while a file is loaded."""
        if len(self.jobs) <= 1:
            return
        if 0 <= index < len(self.jobs):
            self.jobs.pop(index)

    def update_job_name(self, index: int, name: str) -> None:
        self.jobs[index].name = name

    def set_job_mode(self, index: int, mode: str) -> None:
        self.jobs[index].set_mode(mode, self.total_pages)

    def update_job_custom_sequence_text(self, index: int, text: str) -> None:
        self.jobs[index].update_custom_sequence_text(text, self.total_pages)

    def update_job_split_point(self, index: int, value: int | None) -> None:
        self.jobs[index].update_split_point(value, self.total_pages)

    def job_name_errors(self, index: int) -> list[FieldError]:
        job = self.jobs[index]
        others = [j.name for k, j in enumerate(self.jobs) if k != index]
        return job.name_errors(others)

    @property
    def name_conflict_errors(self) -> list[FieldError]:
        errors: list[FieldError] = []
        for index in range(len(self.jobs)):
            errors.extend(self.job_name_errors(index))
        return errors

    @property
    def is_valid(self) -> bool:
        """True once every job has a valid page sequence and a usable,
        unique name — the gate for enabling export."""
        if not self.file_path or not self.jobs:
            return False
        if not all(job.is_valid for job in self.jobs):
            return False
        return not self.name_conflict_errors

    def extract_all(self, dest_dir: str) -> None:
        """Writes every job to '<dest_dir>/<name>.pdf'. Guards on
        is_valid; a mid-batch engine failure is recorded but does not
        stop the remaining jobs, so one bad job doesn't lose the rest.
        Callers driving a UI should dispatch this off the main thread
        (e.g. NiceGUI's run.io_bound) — this method itself has no
        threading/UI awareness."""
        if not self.is_valid or not self.file_path:
            return

        self.is_extracting = True
        self.extraction_errors = []
        self.output_paths = []
        total_jobs = len(self.jobs)
        self.extraction_job_progress = (0, total_jobs)

        for i, job in enumerate(self.jobs):
            name = job.name.strip()
            self.extraction_current_job_name = name
            self.extraction_progress = (0, len(job.computed_page_indices))

            def _progress(current: int, total: int) -> None:
                self.extraction_progress = (current, total)

            dest_path = os.path.join(dest_dir, f"{name}.pdf")
            result = engine.extract_pages(
                self.file_path, job.computed_page_indices, dest_path, progress_cb=_progress
            )

            if result.ok:
                self.output_paths.append(result.value)
            else:
                self.extraction_errors.extend(result.errors)

            self.extraction_job_progress = (i + 1, total_jobs)

        self.extraction_current_job_name = None
        self.is_extracting = False
