# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build recipe for DeskX.

Produces a self-contained desktop bundle so end users never install
Python. Build with ``pyinstaller packaging/DeskX.spec`` from the repo
root, or use the ``packaging/build_windows.ps1`` helper.
"""

import sys
from pathlib import Path

# ``__file__`` is not defined while PyInstaller execs a spec, so anchor
# on the spec path it injects instead.
ROOT = Path(SPECPATH).parent
IS_MAC = sys.platform == "darwin"

APP_NAME = "DeskX"
VERSION = "0.1.0"

# The only runtime file that lives outside the .py sources: the bundled
# sample dataset behind "Try sample data". Sanitized outputs that users
# happened to save next to it are deliberately left out.
datas = [
    (str(ROOT / "src" / "deskx" / "samples" / "sample_employees.csv"), "deskx/samples"),
]

# Qt ships far more than a data tool needs. Dropping these keeps the
# bundle to a sane size; every remaining module is one the app imports.
excluded_qt = [
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
    "PySide6.QtBluetooth", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtLocation",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtNfc",
    "PySide6.QtOpenGLFunctions", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning", "PySide6.QtQml", "PySide6.QtQuick",
    "PySide6.QtQuick3D", "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtSensors",
    "PySide6.QtSerialBus", "PySide6.QtSerialPort", "PySide6.QtSpatialAudio",
    "PySide6.QtSql", "PySide6.QtStateMachine", "PySide6.QtTest",
    "PySide6.QtTextToSpeech", "PySide6.QtUiTools", "PySide6.QtVirtualKeyboard",
    "PySide6.QtWebChannel", "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
]

excludes = excluded_qt + [
    "tkinter",
    "matplotlib",
    "IPython",
    "pytest",
    "pytest_qt",
    "sqlite3",
    "unittest",
]


a = Analysis(
    [str(ROOT / "src" / "deskx" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["deskx"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI app: never flash a terminal window
    disable_windowed_traceback=False,
    argv_emulation=IS_MAC,  # lets macOS "open with" pass the file path
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "packaging" / ("DeskX.png" if IS_MAC else "DeskX.ico")),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

if IS_MAC:
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=str(ROOT / "packaging" / "DeskX.icns"),
        bundle_identifier="com.deskx.app",
        version=VERSION,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
