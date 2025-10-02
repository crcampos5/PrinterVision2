"""Main window housing menus, toolbars, and the image viewer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QDialog

from controllers.scan_table_controller import ScanTableController
from models.image_document import ImageDocument
from models.scan_table_model import ScanTableModel
from utils.qt import numpy_to_qpixmap
from views.editor_viewer import EditorViewer
from views.toolbar import MainToolBar
from views.workspace_dialog import WorkspaceDialog


class MainWindow(QMainWindow):
    """Application main window with top toolbar."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PrinterVision Editor")
        self.resize(1200, 800)
        # Central canvas that handles zooming, panning, and rotation.
        self.viewer = EditorViewer(self)
        self.setCentralWidget(self.viewer)

        self.model_scan_table = ScanTableModel()
        self.ctrl_scan_table = ScanTableController(self.model_scan_table)

        # Data model encapsulating reference, mosaic, and workspace state. 
        self.document = ImageDocument()
        self.toolbar = MainToolBar(self, self.ctrl_scan_table)

        
        
        
        self.addToolBar(self.toolbar)




        self._update_actions_state()
        self._update_status()


    def _update_actions_state(self) -> None:
        self.toolbar.load_tif_action.setEnabled(self.document.has_reference)
        self.toolbar.save_action.setEnabled(self.document.has_output)

    def _update_status(self) -> None:
        # Compose a short status message describing the current session.
        parts: list[str] = []
        if self.document.reference_path is not None:
            parts.append(f"Referencia: {self.document.reference_path.name}")
            parts.append(f"Objetos: {len(self.document.centroids)}")
        mm_per_pixel = self.document.get_mm_per_pixel()
        if mm_per_pixel is not None:
            parts.append(f"Escala: {mm_per_pixel[0]:.3f} mm/px (X), {mm_per_pixel[1]:.3f} mm/px (Y)")
        tile_dims = self.document.get_tile_dimensions_mm()
        if tile_dims is not None:
            parts.append(f"TIF: {tile_dims[0]:.1f} x {tile_dims[1]:.1f} mm")
        message = " | ".join(parts) if parts else "Carga una referencia JPG para comenzar."
        self.statusBar().showMessage(message)
