"""One export job's editing UI: output name, mode, sequence inputs, errors."""
from typing import Callable

from nicegui import ui

from pdf_extractor.state import MODE_CUSTOM_SEQUENCE, MODE_SPLIT_INTERLEAVE, PDFApp
from pdf_extractor.ui import custom_sequence_panel, mode_selector, split_interleave_panel


def build(app_state: PDFApp, index: int, on_remove: Callable[[int], None]) -> None:
    job = app_state.jobs[index]

    with ui.card().classes("w-full gap-2"):
        with ui.row().classes("w-full items-center gap-2"):
            ui.input(
                label="Output name",
                value=job.name,
                on_change=lambda e: app_state.update_job_name(index, e.value or ""),
            ).classes("flex-grow").props("outlined dense")
            if len(app_state.jobs) > 1:
                ui.button(icon="delete", on_click=lambda: on_remove(index)).props(
                    "flat dense round color=negative"
                )

        mode_selector.build(app_state, index)

        custom_column = ui.column().classes("w-full gap-0")
        with custom_column:
            custom_sequence_panel.build(app_state, index)

        split_column = ui.column().classes("w-full gap-0")
        with split_column:
            split_interleave_panel.build(app_state, index)

        def refresh_mode_visibility() -> None:
            current_mode = app_state.jobs[index].mode
            custom_column.set_visibility(current_mode == MODE_CUSTOM_SEQUENCE)
            split_column.set_visibility(current_mode == MODE_SPLIT_INTERLEAVE)

        refresh_mode_visibility()
        ui.timer(0.2, refresh_mode_visibility)

        @ui.refreshable
        def render_errors() -> None:
            all_errors = app_state.jobs[index].validation_errors + app_state.job_name_errors(index)
            for err in all_errors:
                ui.label(err.message).classes("text-red-700 text-xs")

        render_errors()
        ui.timer(0.3, render_errors.refresh)
