"""Input field for the Custom Sequence mode, for one job."""
from nicegui import ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp, index: int) -> None:
    ui.textarea(
        label="Pages (e.g. 1, 5, 10-15)",
        value=app_state.jobs[index].custom_sequence_text,
        on_change=lambda e: app_state.update_job_custom_sequence_text(index, e.value or ""),
    ).classes("w-full").props("outlined")
