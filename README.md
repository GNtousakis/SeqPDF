# SeqPDF (PDF Sequence Extractor)

SeqPDF is a desktop application built with Python and [NiceGUI](https://nicegui.io/) that allows you to easily extract specific page sequences from PDF files, or split and interleave them. It provides a clean, native UI for PDF manipulation without needing complex command-line tools.

## Features

- **Custom Page Sequences**: Extract specific pages or ranges using intuitive syntax (e.g., `1, 5, 10-15`).
- **Page Interleaving**: Seamlessly split a PDF at a specific page and interleave the two halves. Ideal for reconstructing documents scanned as two single-sided stacks (e.g., all odd pages, then all even pages).
- **Native Desktop Experience**: Runs as a local desktop window using `pywebview`.
- **Robust Error Handling**: Clear, structured validation messages for invalid inputs, corrupted files, or encrypted PDFs.

## Prerequisites

- Python 3.11+

## Installation

1. Navigate to the project directory:
   ```bash
   cd pdfmod
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *For development (testing, etc.), install `requirements-dev.txt` as well.*

## Usage

Start the application by running the `main.py` script:

```bash
python main.py
```

This will open a native window titled **PDF Sequence Extractor**.

## Packaging

If you're looking to distribute SeqPDF as a standalone executable (e.g., on Windows), please refer to the [Windows Packaging Notes](packaging/windows/README.md).

## Architecture

The project maintains a strict separation of concerns:
- **`engine.py`**: Pure PDF logic using `pypdf`. Handles PDF I/O, sequence math, and returning structured `Result` objects instead of exceptions.
- **`ui/`**: NiceGUI frontend components that bind directly to engine results and state.
- **`models.py` / `state.py`**: Shared data types and state management for the application.
