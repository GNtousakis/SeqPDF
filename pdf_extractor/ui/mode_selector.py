"""Toggle between Custom Sequence and Split & Interleave modes, for one job."""
from nicegui import ui

from pdf_extractor.state import MODE_CUSTOM_SEQUENCE, MODE_SPLIT_INTERLEAVE, PDFApp


def build(app_state: PDFApp, index: int) -> None:
    ui.toggle(
        {MODE_CUSTOM_SEQUENCE: "Custom Sequence", MODE_SPLIT_INTERLEAVE: "Split & Interleave"},
        value=app_state.jobs[index].mode,
        on_change=lambda e: app_state.set_job_mode(index, e.value),
    ).classes("w-full")
