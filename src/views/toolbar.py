"""Toolbar widget grouping main application actions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar, QFileDialog, QMessageBox, QDialog
from controllers.image_controller import ImageController
from controllers.plantilla_controller import PlantillaController
from controllers.scan_table_controller import ScanTableController
from controllers.selection_handler import SelectionHandler
from utils.tools import resource_path
from views.workspace_dialog import WorkspaceDialog

if TYPE_CHECKING:  # pragma: no cover - hints only
    from ..main_window import MainWindow



ICONS_DIR = resource_path("icons")

class MainToolBar(QToolBar):
    """Toolbar housing the primary window actions."""

    def __init__(self, main_window: MainWindow, 
                 scan_table_ctrl: ScanTableController,
                 image_ctrl: ImageController,
                 plantilla_ctrl: PlantillaController) -> None:
        super().__init__("Main Toolbar", main_window)
        self.main_window = main_window
        self.scan_table_ctrl = scan_table_ctrl
        self.image_ctrl = image_ctrl
        self.plantilla_ctrl = plantilla_ctrl
        self.sel_handler: SelectionHandler = None
        self.setMovable(False)

        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.settings_action = QAction(QIcon(str(ICONS_DIR / "settings.svg")), "Parametros", self)
        self.settings_action.triggered.connect(self.configure_workspace)
        self.addAction(self.settings_action)

        self.open_action = QAction(QIcon(str(ICONS_DIR / "open.svg")), "Cargar Tabla Escaneo", self)
        self.open_action.triggered.connect(self.open_scan_table)
        self.addAction(self.open_action)

        self.load_tif_action = QAction(QIcon(str(ICONS_DIR / "add-image.svg")), "Cargar Imagen", self)
        self.load_tif_action.triggered.connect(self.load_image_item)
        self.addAction(self.load_tif_action)

        self.save_action = QAction(QIcon(str(ICONS_DIR / "save.svg")), "Guardar resultado", self)
        self.save_action.triggered.connect(self.save_result)
        self.addAction(self.save_action)

        self.create_template_action = QAction(QIcon(str(ICONS_DIR / "template-add.svg")), "Crear Plantilla", self)
        self.create_template_action.setEnabled(False)
        self.create_template_action.triggered.connect(self.create_template)
        self.addAction(self.create_template_action)

        self.clone_template_action = QAction(QIcon(str(ICONS_DIR / "template-apply-all.svg")), "Clonar Plantilla", self)
        self.clone_template_action.setEnabled(False)
        self.clone_template_action.triggered.connect(self.clone_template)
        self.addAction(self.clone_template_action)

    def open_scan_table(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen de tabla de escaneo",
            str(Path.cwd()),
            "Imagenes JPG (*.jpg *.jpeg);;Todos los archivos (*.*)",
        )
        if not file_path:
            return
        path = Path(file_path)
        if not self.scan_table_ctrl.load_background(path):
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo cargar la tabla de escaneo o no se detectaron objetos.",
            )
            return
        self.scan_table_ctrl.attach_to_scene(self.main_window.viewer.scene())
        self.main_window._refresh_view()
        self.main_window._update_actions_state()
        self.main_window._update_status()

    
    def load_image_item(self) -> None:
        if not self.scan_table_ctrl._model.has_background():
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
        if not self.image_ctrl.load_image(path):
            QMessageBox.warning(self, "Error", "No se pudo cargar el mosaico .tif seleccionado.")
            return

        self.main_window._refresh_view()
        self.main_window._update_actions_state()
        self.main_window._update_status()

    
    def configure_workspace(self) -> None:
        dialog = WorkspaceDialog(
            self,
            width_mm=self.scan_table_ctrl._model.workspace_width_mm,
            height_mm=self.scan_table_ctrl._model.workspace_height_mm,
        )
        if dialog.exec() == QDialog.Accepted:
            width_mm, height_mm = dialog.values()
            self.scan_table_ctrl.update_workspace(width_mm, height_mm)
            self.main_window._refresh_view()
            self.main_window._update_actions_state()
            self.main_window._update_status()

    def save_result(self) -> None:
        if not self.image_ctrl.has_output():
            QMessageBox.information(self, "Sin resultado", "Genera un resultado antes de guardar.")
            return
        default_name = "resultado.tif"
        image_path = self.image_ctrl._model._image_path
        if image_path is not None:
            default_name = f"{image_path.stem}_clonado.tif"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar imagen resultante",
            str(Path.cwd() / default_name),
            "Imagenes TIF (*.tif *.TIF)",
        )
        if not file_path:
            return
        path = Path(file_path)
        if not self.image_ctrl.save_output(path):
            QMessageBox.warning(self, "Error", "No se pudo guardar la imagen resultante.")
            return
        self.main_window.statusBar().showMessage(f"Imagen guardada en: {path}")

    def create_template(self) -> None:
        ctn = self.sel_handler.selected_contours[0]
        img = self.sel_handler.selected_images[0]
        plantilla_item = self.plantilla_ctrl.create(img, ctn)
    
    def clone_template(self) -> None:
        self.plantilla_ctrl.apply_template()
