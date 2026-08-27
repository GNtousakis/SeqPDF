"""Progress indicator for batch PDF export: which job is running and, for
large jobs, its own page-by-page progress."""
from nicegui import ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp) -> None:
    with ui.column().classes("w-full gap-1") as container:
        job_label = ui.label()
        bar = ui.linear_progress(value=0).props("instant-feedback")
        page_label = ui.label().classes("text-xs text-gray-600")

    container.bind_visibility_from(app_state, "is_extracting")

    def refresh() -> None:
        job_progress = app_state.extraction_job_progress
        if job_progress:
            done, total = job_progress
            name = app_state.extraction_current_job_name
            current = min(done + 1, total)
            suffix = f": {name}" if name else ""
            job_label.text = f"Exporting {current} / {total}{suffix}"

        page_progress = app_state.extraction_progress
        if page_progress:
            current, total = page_progress
            bar.value = current / total if total else 0
            page_label.text = f"{current} / {total} pages"

    ui.timer(0.2, refresh)
