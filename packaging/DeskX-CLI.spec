# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller console build for the DeskX CLI (``deskx.exe``).

Ships beside the GUI so end users get both without installing Python.
Build with ``packaging/build_windows.ps1`` or::

    pyinstaller packaging/DeskX-CLI.spec
"""

from pathlib import Path

ROOT = Path(SPECPATH).parent

datas = [
    (str(ROOT / "src" / "deskx" / "samples" / "sample_employees.csv"), "deskx/samples"),
]

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

a = Analysis(
    [str(ROOT / "src" / "deskx" / "cli" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["deskx", "typer", "click", "shellingham"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_qt + [
        "tkinter",
        "matplotlib",
        "IPython",
        "pytest",
        "pytest_qt",
        "unittest",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="deskx",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "packaging" / "DeskX.ico"),
)
