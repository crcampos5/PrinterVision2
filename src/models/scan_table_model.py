"""Model storing scan table background metadata and pixmap."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from PySide6.QtGui import QPixmap

PixmapSource = Union[QPixmap, str, Path]


class ScanTableModel:
    """Keep track of the scan table background image state."""

    def __init__(self) -> None:
        self._background_path: Path | None = None
        self._background_pixmap: QPixmap | None = None

    @property
    def background_path(self) -> Path | None:
        """Return the original path of the background image if available."""
        return self._background_path

    @property
    def background_pixmap(self) -> QPixmap | None:
        """Return the current background pixmap."""
        return self._background_pixmap

    def has_background(self) -> bool:
        """Check whether a background image is loaded."""
        return self._background_pixmap is not None and not self._background_pixmap.isNull()

    def load_background(self, source: PixmapSource) -> bool:
        """Load a background pixmap from disk or duplicate an existing pixmap."""
        pixmap = self._coerce_pixmap(source)
        if pixmap is None:
            return False
        self._background_pixmap = pixmap
        self._background_path = Path(source) if isinstance(source, (str, Path)) else None
        return True

    def clear_background(self) -> None:
        """Remove the stored background pixmap and associated metadata."""
        self._background_pixmap = None
        self._background_path = None

    @staticmethod
    def _coerce_pixmap(source: PixmapSource) -> Optional[QPixmap]:
        if isinstance(source, QPixmap):
            # Detach so mutations do not affect the original pixmap owner.
            return QPixmap(source)
        path = Path(source)
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None
        return pixmap
