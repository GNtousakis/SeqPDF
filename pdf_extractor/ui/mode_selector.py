"""Toggle between Custom Sequence and Split & Interleave modes."""
from nicegui import ui

from pdf_extractor.state import MODE_CUSTOM_SEQUENCE, MODE_SPLIT_INTERLEAVE, PDFApp


def build(app_state: PDFApp) -> None:
    ui.toggle(
        {MODE_CUSTOM_SEQUENCE: "Custom Sequence", MODE_SPLIT_INTERLEAVE: "Split & Interleave"},
        value=app_state.mode,
        on_change=lambda e: app_state.set_mode(e.value),
    ).classes("w-full")
