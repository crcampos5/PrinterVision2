"""Main window housing menus, toolbars, and the image viewer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QDialog

from controllers.contour_controller import ContourController
from controllers.image_controller import ImageController
from controllers.scan_table_controller import ScanTableController
from controllers.plantilla_controller import PlantillaController
from utils.tools import resource_path
from views.editor_viewer import EditorViewer
from views.toolbar import MainToolBar
from controllers.selection_handler import SelectionHandler

ICONS_DIR = resource_path("icons")

class MainWindow(QMainWindow):
    """Application main window with top toolbar."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PrinterVision v1.0")
        icon_path = ICONS_DIR / "icono.png"   # tu archivo .ico o .png
        self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1200, 800)
        # Central canvas that handles zooming, panning, and rotation.
        self.viewer = EditorViewer(self)
        self.setCentralWidget(self.viewer)

        
        self.ctrl_scan_table = ScanTableController(self)
        self.ctrl_image = ImageController(self, self.ctrl_scan_table)
        self.ctrl_contours = ContourController(self)
        self.ctrl_plantilla = PlantillaController(self.viewer._scene, self.ctrl_contours, self.ctrl_image)

        # Data model encapsulating reference, mosaic, and workspace state. 
        self.toolbar = MainToolBar(self, self.ctrl_scan_table, self.ctrl_image, self.ctrl_plantilla)        
        
        self.ctrl_scan_table.attach_to_scene(self.viewer.scene())
        self.ctrl_image.attach_to_scene(self.viewer.scene()) 
        self.ctrl_contours.attach_to_scene(self.viewer.scene())
        
        self.addToolBar(self.toolbar)

        
        self.ctrl_image.state_changed.connect(self._update_actions_state)

        self.ctrl_scan_table.state_changed.connect(self._update_actions_state)
        self.ctrl_scan_table.state_changed.connect(self._refresh_view)
        self.ctrl_scan_table.state_changed.connect(
            lambda: self.ctrl_contours._on_scan_table_changed(self.ctrl_scan_table),
        )
        self.ctrl_scan_table.state_changed.connect(
            lambda: self.ctrl_image._on_scan_table_changed(self.ctrl_scan_table)
        )
        self.ctrl_scan_table.state_changed.connect(
            lambda: self.ctrl_plantilla._on_scan_table_changed(self.ctrl_scan_table)
        )

        self.selection = SelectionHandler(self, self.ctrl_plantilla, self.ctrl_scan_table.item, self.ctrl_image.item)
        self.selection.attach_to_scene(self.viewer.scene())

        self.selection.selection_changed.connect(self._update_actions_state)
        self.toolbar.sel_handler = self.selection


        self._update_actions_state()
        self._update_status()

    
    def _refresh_view(self) -> None:
        # Sincroniza el item con el modelo por si cambió el pixmap
        self.ctrl_scan_table.refresh()

        mmpp_x = self.ctrl_scan_table._model.mm_per_pixel_x
        mmpp_y = self.ctrl_scan_table._model.mm_per_pixel_y
        self.ctrl_image.set_target_mm_per_pixel(mmpp_x, mmpp_y)

        self.ctrl_image.refresh()
       # Reset de transformaciones de la vista para evitar acumulación de zoom
        self.viewer.reset_view()

        # Asegura que la escena tenga el rect del nuevo background
        item_bg = self.ctrl_scan_table.item
        if item_bg.pixmap() is not None and not item_bg.pixmap().isNull():
            self.viewer.scene().setSceneRect(item_bg.sceneBoundingRect())

            # Encadrar exactamente al nuevo fondo
            self.viewer.fitInView(item_bg, Qt.KeepAspectRatio)


    def _update_actions_state(self, state_sel: int | None = 0) -> None:
        """Actualiza el estado de los botones del toolbar según el estado actual."""
        has_bg = self.ctrl_scan_table._model.has_background()
        has_output =  self.ctrl_image.has_output()

        self.toolbar.load_tif_action.setEnabled(has_bg)
        self.toolbar.save_action.setEnabled(has_output)

        if state_sel == 1:
            self.toolbar.create_template_action.setEnabled(True)
            return
        if state_sel == 2:
            self.toolbar.clone_template_action.setEnabled(True)
            return
        self.toolbar.clone_template_action.setEnabled(False)
        self.toolbar.create_template_action.setEnabled(False)
        #┼self.toolbar.save_action.setEnabled(False)


    def _update_status(self) -> None:
        # Compose a short status message describing the current session.
        parts: list[str] = []
        if self.ctrl_scan_table._model.background_path is not None:
            parts.append(f"Referencia: {self.ctrl_scan_table._model.background_path.name}")
            parts.append(f"Objetos: {len(self.ctrl_contours._items)}")
        
        message = " | ".join(parts) if parts else "Carga una referencia JPG para comenzar."
        self.statusBar().showMessage(message)
