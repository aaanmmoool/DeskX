"""Debug launcher for DeskX — prints diagnostics to console."""
import sys
import traceback

sys.path.insert(0, "src")

print("Step 1: Importing modules...", flush=True)
try:
    from PySide6.QtWidgets import QApplication
    from deskx.gui.main_window import MainWindow
    print("  Imports OK", flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("Step 2: Creating QApplication...", flush=True)
try:
    app = QApplication(sys.argv)
    print(f"  QApp created (platform: {app.platformName()})", flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("Step 3: Creating MainWindow...", flush=True)
try:
    window = MainWindow()
    print("  MainWindow created", flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("Step 4: Showing window...", flush=True)
try:
    window.show()
    window.raise_()
    window.activateWindow()
    print(f"  Window visible: {window.isVisible()}", flush=True)
    print(f"  Window geometry: {window.geometry()}", flush=True)
    print("  Window should now be on screen!", flush=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)

print("Step 5: Entering event loop...", flush=True)
sys.exit(app.exec())
