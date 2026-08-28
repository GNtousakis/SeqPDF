# PyInstaller spec for PDF Sequence Extractor.
#
# Onedir (not onefile) on purpose: onefile unpacks to a temp _MEIPASS dir at
# runtime, which is where NiceGUI's static asset resolution has historically
# broken when frozen. Onedir avoids that whole failure class at the cost of
# a multi-file distribution instead of a single binary. Revisit only if a
# single-file distributable becomes a hard requirement.
#
# Build from the repo root:
#   pyinstaller packaging/pdfmod.spec --noconfirm
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
repo_root = Path(SPECPATH).parent

datas = collect_data_files("nicegui") + collect_data_files("webview")
hiddenimports = collect_submodules("nicegui") + collect_submodules("pypdf")

if sys.platform == "darwin":
    hiddenimports += collect_submodules("objc") + [
        "Foundation",
        "WebKit",
        "Cocoa",
    ]
elif sys.platform == "win32":
    hiddenimports += ["clr_loader", "clr"]

assets_dir = repo_root / "pdf_extractor" / "assets"
if assets_dir.exists():
    datas.append((str(assets_dir), "pdf_extractor/assets"))

a = Analysis(
    [str(repo_root / "main.py")],
    pathex=[str(repo_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PDFSequenceExtractor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(repo_root / "packaging" / "icon.ico") if sys.platform == "win32" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="PDFSequenceExtractor",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="PDF Sequence Extractor.app",
        icon=str(repo_root / "packaging" / "icon.icns") if (repo_root / "packaging" / "icon.icns").exists() else None,
        bundle_identifier="com.pdfmod.pdfsequenceextractor",
    )
