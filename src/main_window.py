"""Main window housing menus, toolbars, and the image viewer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QToolBar, QDialog

from models.image_document import ImageDocument
from utils.qt import numpy_to_qpixmap
from views.editor_viewer import EditorViewer
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

        # Data model encapsulating reference, mosaic, and workspace state. 
        self.document = ImageDocument()
        self._create_toolbar()
        self._update_actions_state()
        self._update_status()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.settings_action = QAction("Parametros", self)
        self.settings_action.triggered.connect(self.configure_workspace)
        toolbar.addAction(self.settings_action)

        self.open_action = QAction("Abrir referencia", self)
        self.open_action.triggered.connect(self.open_image)
        toolbar.addAction(self.open_action)

        self.load_tif_action = QAction("Cargar .tif", self)
        self.load_tif_action.triggered.connect(self.load_tif)
        toolbar.addAction(self.load_tif_action)

        self.save_action = QAction("Guardar resultado", self)
        self.save_action.triggered.connect(self.save_image)
        toolbar.addAction(self.save_action)

    def configure_workspace(self) -> None:
        dialog = WorkspaceDialog(
            self,
            width_mm=self.document.workspace_width_mm,
            height_mm=self.document.workspace_height_mm,
        )
        if dialog.exec() == QDialog.Accepted:
            width_mm, height_mm = dialog.values()
            self.document.update_workspace(width_mm, height_mm)
            self._refresh_view()
            self._update_actions_state()
            self._update_status()

    def open_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen de referencia",
            str(Path.cwd()),
            "Imagenes JPG (*.jpg *.jpeg);;Todos los archivos (*.*)",
        )
        if not file_path:
            return
        path = Path(file_path)
        if not self.document.load_reference(path):
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo cargar la referencia o no se detectaron objetos.",
            )
            return

        self._refresh_view()
        self._update_actions_state()
        self._update_status()

    def load_tif(self) -> None:
        if not self.document.has_reference:
            QMessageBox.information(self, "Referencia requerida", "Carga una referencia primero.")
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen TIF",
            str(Path.cwd()),
            "Imagenes TIF (*.tif *.TIF);;Todos los archivos (*.*)",
        )
        if not file_path:
            return
        path = Path(file_path)
        if not self.document.load_tile(path):
            QMessageBox.warning(self, "Error", "No se pudo cargar el mosaico .tif seleccionado.")
            return

        self._refresh_view()
        self._update_actions_state()
        self._update_status()

    def save_image(self) -> None:
        if not self.document.has_output:
            QMessageBox.information(self, "Sin resultado", "Genera un resultado antes de guardar.")
            return
        default_name = "resultado.tif"
        if self.document.tile_path is not None:
            default_name = f"{self.document.tile_path.stem}_sobre_centroides.tif"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar imagen resultante",
            str(Path.cwd() / default_name),
            "Imagenes TIF (*.tif *.TIF)",
        )
        if not file_path:
            return
        path = Path(file_path)
        if not self.document.save_output(path):
            QMessageBox.warning(self, "Error", "No se pudo guardar la imagen resultante.")
            return
        self.statusBar().showMessage(f"Imagen guardada en: {path}")

    def _refresh_view(self) -> None:
        if self.document.has_output:
            image = self.document.get_output_preview()
            pix = numpy_to_qpixmap(
                image,
                photometric_hint=getattr(self.document, "tile_photometric", None),
                cmyk_order=getattr(self.document, "tile_cmyk_order", None),
                alpha_index=getattr(self.document, "tile_alpha_index", None),
            )
            self.viewer.set_pixmap(pix)
        else:
            image = self.document.get_reference_preview()
            if image is not None:
                # referencia (JPG) no necesita hints
                self.viewer.set_pixmap(numpy_to_qpixmap(image))
            else:
                self.viewer.clear()


    def _update_actions_state(self) -> None:
        self.load_tif_action.setEnabled(self.document.has_reference)
        self.save_action.setEnabled(self.document.has_output)

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
