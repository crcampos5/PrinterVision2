"""Graphics scene item used to display arbitrary pixmaps."""

from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem


class ImageItem(QGraphicsPixmapItem):
    """Thin wrapper around :class:`QGraphicsPixmapItem` for editor images."""

    def __init__(self, pixmap: QPixmap | None = None) -> None:
        super().__init__()
        if pixmap is not None:
            self.setPixmap(pixmap)

    def set_image_pixmap(self, pixmap: QPixmap | None) -> None:
        """Assign ``pixmap`` to the item, clearing it when ``None``."""

        if pixmap is None or pixmap.isNull():
            self.setPixmap(QPixmap())
            return
        self.setPixmap(pixmap)
