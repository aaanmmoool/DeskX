"""DeskX entry point.

Creates the QApplication, applies the initial theme, and shows the
main window.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from deskx.gui.main_window import MainWindow


def main() -> int:
    """Launch the DeskX application."""
    app = QApplication(sys.argv)
    app.setApplicationName("DeskX")
    app.setOrganizationName("DeskX")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
