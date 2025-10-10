"""Entry point helper to launch the editor from the repo root."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


from PySide6.QtGui import QIcon
# Ensure the src/ directory is available for imports when invoking this script directly.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from main_window import MainWindow
from utils.tools import resource_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path("icons") / "icono.png")))
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())
