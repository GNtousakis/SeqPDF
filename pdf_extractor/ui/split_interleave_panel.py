"""Input field for the Split & Interleave mode."""
from nicegui import ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp) -> None:
    number = (
        ui.number(
            label="Split after page",
            min=1,
            on_change=lambda e: app_state.update_split_point(int(e.value) if e.value is not None else None),
        )
        .classes("w-full")
        .props("outlined")
    )

    def refresh_max() -> None:
        if app_state.total_pages:
            number.props(f"max={app_state.total_pages - 1}")

    ui.timer(0.2, refresh_max)
