"""Scene item representing the scan table background image."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem

PixmapSource = Union[QPixmap, str, Path]


class ScanTableItem(QGraphicsPixmapItem):
    """Pixmap item used to display the scan table background.

    The item can be constructed either with a :class:`QPixmap` instance or with
    a path pointing to an image file. Additional helper methods are provided to
    update the background without replacing the item in the scene.
    """

    def __init__(self, pixmap: PixmapSource | None = None, *, z_value: float = -100.0) -> None:
        super().__init__()
        self.setTransformationMode(Qt.SmoothTransformation)
        self.setZValue(z_value)

        if pixmap is not None:
            self.set_background_pixmap(pixmap)

    def set_background_pixmap(self, pixmap: PixmapSource) -> None:
        """Update the background image displayed by the item."""
        self.setPixmap(self._coerce_pixmap(pixmap))

    @staticmethod
    def _coerce_pixmap(pixmap: PixmapSource) -> QPixmap:
        if isinstance(pixmap, QPixmap):
            return pixmap

        image_path = Path(pixmap)
        qpixmap = QPixmap(str(image_path))
        if qpixmap.isNull():
            raise ValueError(f"Unable to load background image from '{image_path}'.")
        return qpixmap
