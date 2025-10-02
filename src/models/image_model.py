"""Model storing the current pixmap shown by an :class:`ImageItem`."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QPixmap


class ImageModel:
    """Lightweight model keeping track of an image pixmap and metadata."""

    def __init__(self) -> None:
        self._image_path: Optional[Path] = None
        self._pixmap: Optional[QPixmap] = None

    @property
    def image_path(self) -> Optional[Path]:
        """Return the path of the currently loaded image."""

        return self._image_path

    @property
    def pixmap(self) -> Optional[QPixmap]:
        """Return the pixmap representing the current image."""

        return self._pixmap

    def has_image(self) -> bool:
        """Whether the model currently stores a non-empty pixmap."""

        return self._pixmap is not None and not self._pixmap.isNull()

    def load_image(self, path: Path) -> bool:
        """Load an image from ``path`` into the model."""

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.clear()
            return False
        self._image_path = Path(path)
        self._pixmap = pixmap
        return True

    def set_pixmap(self, pixmap: QPixmap | None, path: Path | None = None) -> None:
        """Assign a pixmap directly, optionally updating the source ``path``."""

        if pixmap is None or pixmap.isNull():
            self.clear()
            return
        self._pixmap = pixmap
        if path is not None:
            self._image_path = Path(path)

    def clear(self) -> None:
        """Reset the model, removing any stored pixmap and metadata."""

        self._image_path = None
        self._pixmap = None
