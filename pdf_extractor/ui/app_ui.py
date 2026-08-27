"""Top-level page layout: assembles all panels around a single PDFApp
instance. UI events here only update state and call PDFApp methods — no
PDF logic lives in this module or any of its siblings."""
import webview
from nicegui import app, run, ui

from pdf_extractor.state import PDFApp
from pdf_extractor.ui import error_panel, job_panel, progress, upload_panel


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

    async def handle_export_all() -> None:
        window = app.native.main_window
        if window is None:
            ui.notify("Native window is not available.", type="negative")
            return
        result = await window.create_file_dialog(webview.FileDialog.FOLDER)
        if not result:
            return
        dest_dir = result if isinstance(result, str) else result[0]
        await run.io_bound(app_state.extract_all, dest_dir)
        count = len(app_state.output_paths)
        if count and not app_state.extraction_errors:
            ui.notify(f"Exported {count} PDF{'s' if count != 1 else ''} to {dest_dir}", type="positive")
        elif count:
            ui.notify(f"Exported {count} PDF(s), but some exports failed.", type="warning")
        else:
            ui.notify("Failed to export PDFs.", type="negative")

    ui.label("PDF Sequence Extractor").classes("text-xl font-bold")

    with ui.column().classes("w-full max-w-xl mx-auto gap-4 p-4"):
        upload_panel.build(app_state)

        jobs_container = ui.column().classes("w-full gap-4")

        def handle_add_job() -> None:
            app_state.add_job()
            render_jobs.refresh()

        def handle_remove_job(index: int) -> None:
            app_state.remove_job(index)
            render_jobs.refresh()

        @ui.refreshable
        def render_jobs() -> None:
            if not app_state.file_path:
                return
            for index in range(len(app_state.jobs)):
                job_panel.build(app_state, index, on_remove=handle_remove_job)
            ui.button("+ Add another export", on_click=handle_add_job).props("outline").classes("w-full")

        with jobs_container:
            render_jobs()

        # Loading a file rebuilds app_state.jobs directly (outside any
        # button handler this page controls), so watch its length rather
        # than relying on an explicit refresh call from upload_panel.
        last_job_count = {"n": len(app_state.jobs)}

        def sync_jobs_on_file_load() -> None:
            if len(app_state.jobs) != last_job_count["n"]:
                last_job_count["n"] = len(app_state.jobs)
                render_jobs.refresh()

        ui.timer(0.2, sync_jobs_on_file_load)

        error_panel.build(app_state)
        progress.build(app_state)

        export_button = ui.button("Export All...", on_click=handle_export_all)
        export_button.bind_enabled_from(app_state, "is_valid")
