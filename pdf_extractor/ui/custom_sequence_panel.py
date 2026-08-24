"""Input field for the Custom Sequence mode."""
from nicegui import ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp) -> None:
    ui.textarea(
        label="Pages (e.g. 1, 5, 10-15)",
        on_change=lambda e: app_state.update_custom_sequence_text(e.value or ""),
    ).classes("w-full").props("outlined")
