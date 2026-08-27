"""Input field for the Split & Interleave mode, for one job."""
from nicegui import ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp, index: int) -> None:
    number = (
        ui.number(
            label="Split after page",
            min=1,
            value=app_state.jobs[index].split_point_input,
            on_change=lambda e: app_state.update_job_split_point(
                index, int(e.value) if e.value is not None else None
            ),
        )
        .classes("w-full")
        .props("outlined")
    )

    def refresh_max() -> None:
        if app_state.total_pages:
            number.props(f"max={app_state.total_pages - 1}")

    ui.timer(0.2, refresh_max)
