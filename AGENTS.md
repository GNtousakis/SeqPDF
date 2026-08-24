# AGENTS.md

## Commands

- Activate venv first: `source venv/bin/activate` (Python 3.11).
- Run app: `python main.py` (opens native pywebview window).
- Tests: `pytest` (config in `pyproject.toml`; no lint/typecheck setup exists).
- Single test: `pytest tests/test_engine_io.py::test_name`.
- macOS build: `packaging/build_macos.sh` from repo root (runs PyInstaller with `packaging/pdfmod.spec`; output in `dist/`). Launch the binary directly, not via Finder, to see startup errors.

## Architecture

- Strict layering: `pdf_extractor/engine.py`, `validation.py`, and `models.py` are pure PDF logic (pypdf only). **Never import NiceGUI/pywebview into engine modules** — tests depend on them staying importable without a GUI.
- Engine functions return `Result` objects (`models.py`) instead of raising for expected failures (bad input, corrupt/encrypted files). UI handlers bind to these results; don't add try/except in event handlers.
- Page sequences are 0-indexed internally; user input is 1-indexed print-style (`1, 5, 10-15`). Duplicate page references are rejected as errors, not deduplicated.
- Entry point is `main.py` → `pdf_extractor/ui/app_ui.py:register()`. `multiprocessing.freeze_support()` in `main.py` is required for PyInstaller builds — don't remove it.

## Testing

- Test fixtures generate real PDFs on the fly in `tests/conftest.py` (`ten_page_pdf`, `encrypted_pdf`, `corrupt_pdf`, `missing_pdf`); use these instead of committing binary fixtures.
