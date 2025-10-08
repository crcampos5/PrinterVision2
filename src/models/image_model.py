# image_model.py
"""Model storing the current QImage preview for an :class:`ImageItem`."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
from PySide6.QtGui import QImage

from utils.file_manager import load_tif, to_rgba8_preview


class ImageModel:
    """Lightweight model keeping a master pixel buffer and a QImage preview."""

    def __init__(self) -> None:
        # Ruta y previsualización
        self._image_path: Optional[Path] = None
        self._qimage: Optional[QImage] = None

        # Buffer maestro y metadatos físicos / de color
        self.pixels: Optional[np.ndarray] = None          # HxWxC, dtype intacto
        self.dpi_x: Optional[float] = None
        self.dpi_y: Optional[float] = None
        self.width_mm: Optional[float] = None
        self.height_mm: Optional[float] = None
        self.photometric: Optional[str] = None            # 'rgb' | 'minisblack' | 'separated' ...
        self.cmyk_order: Optional[Tuple[int, int, int, int]] = None
        self.alpha_index: Optional[int] = None
        self.icc_profile: Optional[bytes] = None
        self.ink_names: Optional[List[str]] = None

        self.scale_sx = None
        self.scale_sy = None

    @property
    def image_path(self) -> Optional[Path]:
        return self._image_path

    @property
    def qimage(self) -> Optional[QImage]:
        return self._qimage

    def has_image(self) -> bool:
        return self._qimage is not None and not self._qimage.isNull()

    def load_image(self, path: Path) -> bool:
        """
        Carga un TIF con file_manager.load_tif (mantiene dtype original en `self.pixels`)
        y crea una previsualización RGBA8 mediante utils.file_manager.to_rgba8_preview.
        """
        data = load_tif(path)
        if not data or data.get("pixels") is None:
            self.clear()
            return False

        # 1) Ruta y metadatos (buffer maestro intacto)
        self._image_path = Path(path)
        self.pixels = data["pixels"]
        self.dpi_x = data["dpi_x"]
        self.dpi_y = data["dpi_y"]
        self.width_mm = data["width_mm"]
        self.height_mm = data["height_mm"]
        self.photometric = data["photometric"]
        self.cmyk_order = data["cmyk_order"]
        self.alpha_index = data["alpha_index"]
        self.icc_profile = data["icc_profile"]
        self.ink_names = data["ink_names"]

        # 2) Preview RGBA8 (conserva transparencia si existe)
        rgba8 = to_rgba8_preview(self.pixels, self.photometric, self.cmyk_order, self.alpha_index)
        if rgba8 is not None and rgba8.ndim == 3 and rgba8.shape[2] == 4:
            h, w = rgba8.shape[:2]
            self._qimage = QImage(rgba8.data, w, h, rgba8.strides[0], QImage.Format_RGBA8888).copy()
        else:
            self._qimage = None

        return True

    def clear(self) -> None:
        self._image_path = None
        self._qimage = None
        self.pixels = None
        self.dpi_x = None
        self.dpi_y = None
        self.width_mm = None
        self.height_mm = None
        self.photometric = None
        self.cmyk_order = None
        self.alpha_index = None
        self.icc_profile = None
        self.ink_names = None
