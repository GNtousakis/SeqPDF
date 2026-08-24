import multiprocessing

from nicegui import ui

from pdf_extractor.ui.app_ui import register


def main() -> None:
    register()
    ui.run(native=True, window_size=(900, 700), title="PDF Sequence Extractor", reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    # Required when frozen: native mode spawns a subprocess for the webview
    # process, and without freeze_support() the frozen executable tries to
    # re-parse its own compiled binary as Python source on relaunch.
    multiprocessing.freeze_support()
    main()
