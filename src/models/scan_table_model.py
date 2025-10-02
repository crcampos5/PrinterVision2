"""Model storing scan table (background) metadata and pixmap."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Tuple

import numpy as np
from PySide6.QtGui import QPixmap

from controllers.detection import detect_centroids
from utils.file_manager import load_scan_table


class ScanTableModel:
    """
    Mantiene el estado de la mesa de escaneo (scan table):
    - Imagen base y pixmap
    - Centroides detectados
    - Escalas en mm/px
    """

    def __init__(self) -> None:
        self.scan_table_path: Optional[Path] = None
        self.scan_table_image: Optional[np.ndarray] = None
        self.scan_table_pixmap: Optional[QPixmap] = None

        self.centroids: List[Tuple[float, float]] = []

        self.workspace_width_mm: float = 480.0
        self.workspace_height_mm: float = 600.0

        self.mm_per_pixel_x: Optional[float] = None
        self.mm_per_pixel_y: Optional[float] = None

        self.min_area: float = 50.0

    @property
    def background_path(self) -> Optional[Path]:
        return self.scan_table_path

    @property
    def background_pixmap(self) -> Optional[QPixmap]:
        return self.scan_table_pixmap

    def has_background(self) -> bool:
        return self.scan_table_pixmap is not None and not self.scan_table_pixmap.isNull()

    def load_background(self, path: Path) -> bool:
        data = load_scan_table(path)
        if data is None or data is None:
            self.clear_background()
            return False

        image = data
        _, centroids = detect_centroids(image, self.min_area)

        self.scan_table_path = Path(path)
        self.scan_table_image = image
        self.scan_table_pixmap = QPixmap(str(self.scan_table_path))
        self.centroids = centroids

        if self.scan_table_pixmap.isNull():
            self.scan_table_pixmap = None

        self._recompute_mm_per_pixel()
        return True

    def clear_background(self) -> None:
        self.scan_table_path = None
        self.scan_table_image = None
        self.scan_table_pixmap = None
        self.centroids = []
        self.mm_per_pixel_x = None
        self.mm_per_pixel_y = None

    def _recompute_mm_per_pixel(self) -> None:
        img = self.scan_table_image
        if img is None or img.size == 0:
            self.mm_per_pixel_x = None
            self.mm_per_pixel_y = None
            return
        h, w = img.shape[:2]
        self.mm_per_pixel_x = self.workspace_width_mm / float(w)
        self.mm_per_pixel_y = self.workspace_height_mm / float(h)
