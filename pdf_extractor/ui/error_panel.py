"""Renders file-load/extraction errors from PDFApp state. Per-job
validation and naming errors are rendered inline by job_panel instead."""
from nicegui import ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp) -> None:
    @ui.refreshable
    def render() -> None:
        all_errors = app_state.file_load_errors + app_state.extraction_errors
        if not all_errors:
            return
        with ui.card().classes("w-full bg-red-50 border border-red-300"):
            for err in all_errors:
                ui.label(err.message).classes("text-red-700 text-sm")

    render()
    ui.timer(0.3, render.refresh)
