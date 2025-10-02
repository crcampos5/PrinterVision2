"""Toolbar widget grouping main application actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar

if TYPE_CHECKING:  # pragma: no cover - hints only
    from ..main_window import MainWindow


class MainToolBar(QToolBar):
    """Toolbar housing the primary window actions."""

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__("Main Toolbar", main_window)
        self.setMovable(False)

        self.settings_action = QAction("Parametros", self)
        self.settings_action.triggered.connect(main_window.configure_workspace)
        self.addAction(self.settings_action)

        self.open_action = QAction("Abrir referencia", self)
        self.open_action.triggered.connect(main_window.open_image)
        self.addAction(self.open_action)

        self.load_tif_action = QAction("Cargar .tif", self)
        self.load_tif_action.triggered.connect(main_window.load_tif)
        self.addAction(self.load_tif_action)

        self.save_action = QAction("Guardar resultado", self)
        self.save_action.triggered.connect(main_window.save_image)
        self.addAction(self.save_action)
