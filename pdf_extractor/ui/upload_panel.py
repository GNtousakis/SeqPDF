"""Drag-and-drop file upload + immediate page-count feedback."""
import tempfile

from nicegui import events, ui

from pdf_extractor.state import PDFApp


def build(app_state: PDFApp) -> None:
    async def handle_upload(e: events.UploadEventArguments) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await e.file.read()
            tmp.write(content)
            temp_path = tmp.name
        app_state.load_file(temp_path)
        upload.reset()

    upload = (
        ui.upload(on_upload=handle_upload, auto_upload=True, label="Drop a PDF here or click to browse")
        .props("accept=.pdf")
        .classes("w-full")
    )

    page_count_label = ui.label().classes("text-sm text-gray-600")
    encrypted_label = ui.label(
        "Note: this PDF was encrypted but opened with an empty password."
    ).classes("text-amber-600 text-xs")
    encrypted_label.bind_visibility_from(app_state, "is_encrypted")

    def refresh() -> None:
        page_count_label.text = f"{app_state.total_pages} pages loaded" if app_state.total_pages else ""

    ui.timer(0.2, refresh)
