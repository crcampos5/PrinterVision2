# controllers/plantilla_controller.py
from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsScene

from views.scene_items.plantilla_item import PlantillaItem
from views.scene_items.image_item import ImageItem
from views.scene_items.contour_item import ContourItem


class PlantillaController:
    """Controlador mínimo: crea PlantillaItem y lo centra sobre el contorno."""

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene

    def create(self, image_item: ImageItem, contour_item: ContourItem) -> PlantillaItem:
        plantilla = PlantillaItem(image_item=image_item, contour_item=contour_item)
        self._scene.addItem(plantilla)

        # centro del contorno en coords de escena
        #target_center: QPointF = contour_item.sceneBoundingRect().center()
        # centro actual del compuesto en coords de escena
        #current_center: QPointF = plantilla.mapToScene(plantilla.boundingRect().center())
        # trasladar para alinear centro a centro
        #delta = target_center - current_center
        #plantilla.setPos(plantilla.pos() + delta)

        return plantilla
