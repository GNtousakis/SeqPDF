"""Top-level page layout: assembles all panels around a single PDFApp
instance. UI events here only update state and call PDFApp methods — no
PDF logic lives in this module or any of its siblings."""
import webview
from nicegui import app, run, ui

from pdf_extractor.state import MODE_CUSTOM_SEQUENCE, MODE_SPLIT_INTERLEAVE, PDFApp
from pdf_extractor.ui import (
    custom_sequence_panel,
    error_panel,
    mode_selector,
    progress,
    split_interleave_panel,
    upload_panel,
)


def register() -> None:
    """Registers the '/' route. Must be called (imported) before ui.run().

    Explicit @ui.page registration (rather than building the UI eagerly at
    import time) matters even for this single-window native app: without a
    registered route, NiceGUI falls back to re-executing the entry script
    itself to render the page, which reads sys.argv[0] as Python source —
    fatal once frozen, since sys.argv[0] is then the compiled binary.
    """

    @ui.page("/")
    def index() -> None:
        _build_page()


def _build_page() -> None:
    app_state = PDFApp()

    async def handle_save() -> None:
        window = app.native.main_window
        if window is None:
            ui.notify("Native window is not available.", type="negative")
            return
        result = window.create_file_dialog(
            webview.SAVE_DIALOG, save_filename="extracted.pdf", file_types=("PDF Files (*.pdf)",)
        )
        if not result:
            return
        dest_path = result if isinstance(result, str) else result[0]
        await run.io_bound(app_state.extract, dest_path)
        if app_state.output_path:
            ui.notify(f"Saved to {app_state.output_path}", type="positive")
        else:
            ui.notify("Failed to save PDF.", type="negative")

    ui.label("PDF Sequence Extractor").classes("text-xl font-bold")

    with ui.column().classes("w-full max-w-xl mx-auto gap-4 p-4"):
        upload_panel.build(app_state)
        mode_selector.build(app_state)

        custom_column = ui.column().classes("w-full")
        with custom_column:
            custom_sequence_panel.build(app_state)

        split_column = ui.column().classes("w-full")
        with split_column:
            split_interleave_panel.build(app_state)

        def refresh_mode_visibility() -> None:
            custom_column.set_visibility(app_state.mode == MODE_CUSTOM_SEQUENCE)
            split_column.set_visibility(app_state.mode == MODE_SPLIT_INTERLEAVE)

        refresh_mode_visibility()
        ui.timer(0.2, refresh_mode_visibility)

        error_panel.build(app_state)
        progress.build(app_state)

        save_button = ui.button("Save As...", on_click=handle_save)
        save_button.bind_enabled_from(app_state, "is_valid")
