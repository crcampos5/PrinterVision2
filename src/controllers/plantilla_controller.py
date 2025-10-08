# controllers/plantilla_controller.py
from __future__ import annotations
import math

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from controllers.contour_controller import ContourController
from controllers.image_controller import ImageController
from controllers.scan_table_controller import ScanTableController
from views.scene_items.plantilla_item import PlantillaItem
from views.scene_items.image_item import ImageItem
from views.scene_items.contour_item import ContourItem


class PlantillaController:
    """Controlador mínimo: crea PlantillaItem y lo centra sobre el contorno."""

    def __init__(self, scene: QGraphicsScene, contour_ctrl: ContourController, image_ctrl: ImageController) -> None:
        self._scene = scene
        self.contour_ctrl = contour_ctrl
        self.image_ctrl = image_ctrl
        self.angle_off_set = None
        self.pos_off_set = None
        self._template_item: PlantillaItem | None = None

    def create(self, image_item: ImageItem, contour_item: ContourItem) -> PlantillaItem:
        plantilla = PlantillaItem(image_item=image_item, contour_item=contour_item)
        self._scene.addItem(plantilla)

        self.angle_off_set = 360 - contour_item.model.angle_o + image_item.rotation()

        rect_center = image_item.boundingRect().center()
        scene_center = image_item.mapToScene(rect_center)

        ctn_pos = QPointF(contour_item.model.cx_o,contour_item.model.cy_o)

        self.pos_off_set = scene_center - ctn_pos
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
        
        sx = self.image_ctrl._model.scale_sx
        sy = self.image_ctrl._model.scale_sy

        base_transform = template_image.transform()
        flags = template_image.flags()
        z_value = template_image.zValue()

        for contour in self.contour_ctrl._items:
            if contour is template_contour:
                continue

            new_image = ImageItem()
            new_image.set_image_pixmap(pixmap)
            new_image.setTransform(base_transform, False)
            new_image.setTransformOriginPoint(new_image.boundingRect().center())
            new_image.setFlags(flags)
            new_image.setZValue(z_value)

            angle = contour.model.angle_o + self.angle_off_set
            new_image.setRotation(angle)
            
            ctn_cen = QPointF(contour.model.cx_o,contour.model.cy_o)
            
            br = new_image.boundingRect()
            w = br.width() * sx
            h = br.height() * sy

            center_offset = QPointF(w / 2, h / 2)

            rot_off_set = self.rotar_vector(self.pos_off_set, angle)
            new_pos = ctn_cen - center_offset + rot_off_set
            
            if isinstance(new_pos, QPointF):
                new_image.setPos(new_pos)
            else:
                new_image.setPos(QPointF(new_pos))

            new_image.setFlag(QGraphicsItem.ItemIsSelectable, True)

            self._scene.addItem(new_image)


    def rotar_vector(self, v: QPointF, angulo_deg: float) -> QPointF:
        a = math.radians(angulo_deg)
        cos_a, sin_a = math.cos(a), math.sin(a)
        x = v.x() * cos_a - v.y() * sin_a
        y = v.x() * sin_a + v.y() * cos_a
        return QPointF(x, y)

