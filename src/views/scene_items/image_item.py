"""Elemento de escena para mostrar una imagen."""

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem


class ImagenItem(QGraphicsPixmapItem):
    """Item gráfico sencillo que muestra un :class:`QPixmap`."""

    def __init__(self, pixmap: QPixmap | None = None) -> None:
        super().__init__()
        if pixmap is not None:
            self.setPixmap(pixmap)
