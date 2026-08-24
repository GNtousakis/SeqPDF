# Windows packaging notes

Decided: bundle the WebView2 Evergreen Bootstrapper rather than assume the
runtime is preinstalled (some Windows 10 / locked-down corporate machines
don't have it).

1. Download `MicrosoftEdgeWebView2Setup.exe` from Microsoft's WebView2
   developer page and place it in this directory.
2. Wrap `dist/PDFSequenceExtractor/` (output of `build_windows.ps1`) in an
   installer — Inno Setup is a reasonable free default — and add a
   prerequisite/custom action step that silently runs
   `MicrosoftEdgeWebView2Setup.exe /silent /install` before the app files
   are placed.
3. Test on a clean Windows VM/machine with WebView2 manually uninstalled —
   testing only on a dev machine that already has it (most do) will not
   catch a broken bootstrap step.

This keeps the WebView2 check-and-install at install time, not app launch
time, so `main.py` stays free of Windows-specific installer logic.
