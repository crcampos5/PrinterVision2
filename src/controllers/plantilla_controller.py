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
        self._template_item: PlantillaItem | None = None

    def create(self, image_item: ImageItem, contour_item: ContourItem) -> PlantillaItem:
        plantilla = PlantillaItem(image_item=image_item, contour_item=contour_item)
        self._scene.addItem(plantilla)

        self.angle_off_set = 360 - contour_item.model.angle_o + image_item.rotation()
        self.pos_off_set = contour_item.pos() - image_item.pos()
        self._template_item = plantilla

        return plantilla

    def apply_template(self):
        if self._scene is None:
            return

        if self._template_item is None:
            return

        template_image = self._template_item.image_item
        template_contour = self._template_item.contour_item

        if template_image is None:
            return

        pixmap = template_image.pixmap()
        if pixmap.isNull():
            return

        if self.angle_off_set is None or self.pos_off_set is None:
            return

        base_transform = template_image.transform()
        origin_point = template_image.transformOriginPoint()
        flags = template_image.flags()
        z_value = template_image.zValue()

        for contour in self.contour_ctrl._items:
            if contour is template_contour:
                continue

            new_image = ImageItem()
            new_image.set_image_pixmap(pixmap)
            new_image.setTransform(base_transform, False)
            new_image.setTransformOriginPoint(origin_point)
            new_image.setFlags(flags)
            new_image.setZValue(z_value)

            angle = 360 - contour.model.angle_o + self.angle_off_set
            new_image.setRotation(angle)

            new_pos = contour.pos() - self.pos_off_set
            if isinstance(new_pos, QPointF):
                new_image.setPos(new_pos)
            else:
                new_image.setPos(QPointF(new_pos))

            self._scene.addItem(new_image)

        print("aplicando clonacion")
