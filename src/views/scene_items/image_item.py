"""Graphics scene item used to display arbitrary pixmaps."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsSceneWheelEvent, QGraphicsItem


class ImageItem(QGraphicsPixmapItem):
    """Thin wrapper around :class:`QGraphicsPixmapItem` for editor images."""

    def __init__(self, pixmap: QPixmap | None = None) -> None:
        super().__init__()
        self.controller = None
        self.deletable = True
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        if pixmap is not None:
            self.setPixmap(pixmap)

    def set_image_pixmap(self, pixmap: QPixmap | None) -> None:
        """Assign ``pixmap`` to the item, clearing it when ``None``."""
        if pixmap is None or pixmap.isNull():
            self.setPixmap(QPixmap())
            return
        self.setPixmap(pixmap)

    def on_selected(self):
        if self.controller is None :
            return
        self.controller.on_selection_changed()

    def wheelEvent(self, event: QGraphicsSceneWheelEvent) -> None:
        # Solo si está seleccionado y el usuario mantiene Shift
        if self.isSelected() and (event.modifiers() & Qt.ShiftModifier):
            br = self.boundingRect()
            self.setTransformOriginPoint(br.center())
            step = 5.0 if event.delta() > 0 else -5.0
            self.setRotation(self.rotation() + step)
            event.accept()
            return
        # En cualquier otro caso, comportamiento por defecto
        super().wheelEvent(event)