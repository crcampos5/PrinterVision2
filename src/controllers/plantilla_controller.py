# controllers/plantilla_controller.py
from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsScene

from controllers.contour_controller import ContourController
from views.scene_items.plantilla_item import PlantillaItem
from views.scene_items.image_item import ImageItem
from views.scene_items.contour_item import ContourItem


class PlantillaController:
    """Controlador mínimo: crea PlantillaItem y lo centra sobre el contorno."""

    def __init__(self, scene: QGraphicsScene, contour_ctrl: ContourController) -> None:
        self._scene = scene
        self.contour_ctrl = contour_ctrl
        self.angle_off_set = None
        self.pos_off_set = None

    def create(self, image_item: ImageItem, contour_item: ContourItem) -> PlantillaItem:
        plantilla = PlantillaItem(image_item=image_item, contour_item=contour_item)
        self._scene.addItem(plantilla)

        self.angle_off_set = 360 - contour_item.model.angle_o + image_item.rotation()
        self.pos_off_set = contour_item.pos() - image_item.pos()

        return plantilla
    
    def apply_template(self):

        contours = self.contour_ctrl._items
        print("aplicando clonacion")
