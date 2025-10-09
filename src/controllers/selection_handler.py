from __future__ import annotations
from shiboken6 import isValid
from typing import Optional
from PySide6.QtCore import QObject, Signal, QEvent, Qt
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from controllers.plantilla_controller import PlantillaController
from views.scene_items.contour_item import ContourItem
from views.scene_items.image_item import ImageItem
from views.scene_items.plantilla_item import PlantillaItem

class SelectionHandler(QObject):
    """ En las senales  
    0 Predeterminado
    1 Es la seleccion de un ImageItem y un ContourItem
    2 Es seleccionado una plantilla
    """
    selection_changed = Signal(int)

    def __init__(self, parent: QObject,
                ctrl_plantilla: PlantillaController,
                scan_table_item: QGraphicsItem, 
                image_item: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self._scene: Optional[QGraphicsScene] = None
        self._bg = scan_table_item
        self._img = image_item
        self._ctrl_plantilla = ctrl_plantilla
        self.selected_images: list[ImageItem] = []
        self.selected_contours: list[ContourItem] = []
        self.selected_templates: list[PlantillaItem] = []

    def attach_to_scene(self, scene: QGraphicsScene | None) -> None:
        if self._scene is scene:
            return
        if self._scene is not None:
            try:
                self._scene.removeEventFilter(self)
                self._scene.selectionChanged.disconnect(self.on_selection_changed)
            except Exception:
                pass
        self._scene = scene
        if scene is None:
            return
        # Flags básicos
        self._bg.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self._bg.setFlag(QGraphicsItem.ItemIsMovable, False)
        self._img.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self._img.setFlag(QGraphicsItem.ItemIsMovable, True)
        # Eventos básicos
        scene.installEventFilter(self)
        scene.selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        if (self._scene is None) or (not isValid(self._scene)):
            return
        items = self._scene.selectedItems()
        # Clasificamos
        self.selected_images = [it for it in items if isinstance(it, ImageItem)]
        self.selected_contours = [it for it in items if isinstance(it, ContourItem)]
        self.selected_templates = [it for it in items if isinstance(it, PlantillaItem)]

        n_img = len(self.selected_images)
        n_contour = len(self.selected_contours)
        n_templates = len(self.selected_templates)
        estado_seleccion = 0
        # Diagnóstico
        if n_img == 1 and n_contour == 0 and n_templates == 0:
            image = self.selected_images[0]
            image.on_selected()
        elif n_img == 0 and n_contour == 1 and n_templates == 0:
            ctn = self.selected_contours[0]
            ctn.on_selected()
        elif n_img == 1 and n_contour == 1 and n_templates == 0:
            estado_seleccion = 1
        elif  n_templates == 1:
            estado_seleccion = 2
        else: pass
            #print(f"👉 Selección múltiple (ImageItems={n_img}, Contours={n_contour}, Total={len(items)})")

        self.selection_changed.emit(estado_seleccion)
        

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # solo lo mínimo
        return False
