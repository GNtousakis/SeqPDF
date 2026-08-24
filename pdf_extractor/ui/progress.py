"""Progress indicator for large-PDF extraction."""
from nicegui import ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp) -> None:
    with ui.column().classes("w-full") as container:
        bar = ui.linear_progress(value=0).props("instant-feedback")
        label = ui.label()

    container.bind_visibility_from(app_state, "is_extracting")

    def refresh() -> None:
        progress = app_state.extraction_progress
        if progress:
            current, total = progress
            bar.value = current / total if total else 0
            label.text = f"{current} / {total} pages"

    ui.timer(0.2, refresh)
