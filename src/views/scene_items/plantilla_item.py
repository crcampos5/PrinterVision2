# src/views/scene_items/plantilla_item.py
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem, QStyleOptionGraphicsItem, QWidget


class PlantillaItem(QGraphicsObject):
    """Contenedor mínimo: une ImageItem + ContourItem, se puede mover, NO rota.
       Dibuja su boundingRect en verde para referencia visual.
    """
    def __init__(self, image_item: QGraphicsItem, contour_item: QGraphicsItem, parent=None):
        super().__init__(parent)
        self.image_item = image_item
        self.contour_item = contour_item

        # Parentar hijos al contenedor
        self.image_item.setParentItem(self)
        self.contour_item.setParentItem(self)

        # Hijos sin interacción directa
        for ch in (self.image_item, self.contour_item):
            ch.setFlag(QGraphicsItem.ItemIsSelectable, False)
            ch.setFlag(QGraphicsItem.ItemIsMovable, False)
            ch.setFlag(QGraphicsItem.ItemIsFocusable, False)

        # Este contenedor solo se mueve (NO rotación)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsFocusable, False)

    # --- Geometría ---
    def boundingRect(self) -> QRectF:
        img_r = self.image_item.mapRectToParent(self.image_item.boundingRect())
        cnt_r = self.contour_item.mapRectToParent(self.contour_item.boundingRect())
        return img_r.united(cnt_r)

    # --- Pintado (marco verde del bounding) ---
    def paint(self, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        painter: QPainter = option.painter
        pen = QPen(QColor(0, 200, 0))
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.boundingRect())

    # Bloquear rotación
    def setRotation(self, angle: float) -> None:
        return
