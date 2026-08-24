# Build the Windows app. Run from the repo root with the venv active.
#
# WebView2 policy (decided): bundle the Evergreen Bootstrapper rather than
# assume the runtime is preinstalled. This script only builds the frozen
# app; the bootstrapper is wired in as an installer prerequisite (Inno
# Setup or equivalent — see packaging/windows/README below), not invoked
# from main.py, so app code stays free of Windows-specific install logic.
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
pyinstaller packaging/pdfmod.spec --noconfirm

Write-Host ""
Write-Host "Built: dist/PDFSequenceExtractor/PDFSequenceExtractor.exe"
Write-Host "Launch it directly from a terminal (not double-click) to see startup errors."
Write-Host ""
Write-Host "Before shipping: wrap dist/PDFSequenceExtractor/ in an installer that runs"
Write-Host "packaging/windows/MicrosoftEdgeWebView2Setup.exe (Evergreen Bootstrapper) as a"
Write-Host "prerequisite step, and test on a clean VM without WebView2 preinstalled."
