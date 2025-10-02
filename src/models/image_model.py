# image_model.py
"""Model storing the current pixmap shown by an :class:`ImageItem`."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
from PySide6.QtGui import QPixmap, QImage

from utils.file_manager import load_tif


class ImageModel:
    """Lightweight model keeping track of an image pixmap and metadata."""

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
        Carga un TIF con file_manager.load_tif manteniendo dtype original en `self.pixels`.
        Genera una previsualización QImage (RGB8) sin alterar `self.pixels`.
        """
        data = load_tif(path)
        if not data or data.get("pixels") is None:
            self.clear()
            return False

        # --- 1) Ruta y metadatos (buffer maestro intacto) ---
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

        # --- 2) Construir preview QImage (RGB8) desde `pixels` ---
        import numpy as np
        arr = self.pixels

        # Normalización a uint8 para preview (sin tocar `pixels`)
        x = arr.astype(np.float32, copy=False)
        if x.size == 0:
            self._qimage = None
            return True

        xmax = float(np.nanmax(x))
        xmin = float(np.nanmin(x))
        if xmax <= 1.05:                 # típico float 0..1
            x = np.clip(x, 0.0, 1.0) * 255.0
        elif xmax > 255.0:               # típico 0..65535 o float amplio
            x = np.clip(x, 0.0, 65535.0) / 257.0
        else:
            rng = xmax - xmin
            if rng <= 0.0:
                x = np.zeros_like(x, dtype=np.float32)
            else:
                x = (x - xmin) * (255.0 / rng)

        y = np.clip(x, 0.0, 255.0).round().astype(np.uint8)

        # Pasar a RGB8 (manejo CMYK aproximado para preview)
        if y.ndim == 2:
            rgb8 = np.repeat(y[..., None], 3, axis=2)
            fmt = QImage.Format_RGB888
            h, w = rgb8.shape[:2]
            qimg = QImage(rgb8.data, w, h, rgb8.strides[0], fmt).copy()
            self._qimage = qimg
            return True

        if y.ndim == 3:
            h, w, c = y.shape

            # CMYK → RGB para preview (aproximado)
            if self.photometric == "separated" and c >= 4:
                order = self.cmyk_order if self.cmyk_order else (0, 1, 2, 3)
                C, M, Y, K = [y[..., order[i]].astype(np.float32) / 255.0 for i in range(4)]
                R = (1.0 - np.minimum(1.0, C + K))
                G = (1.0 - np.minimum(1.0, M + K))
                B = (1.0 - np.minimum(1.0, Y + K))
                rgb8 = np.stack(
                    [(R * 255.0).round().astype(np.uint8),
                    (G * 255.0).round().astype(np.uint8),
                    (B * 255.0).round().astype(np.uint8)], axis=2
                )
                fmt = QImage.Format_RGB888
                qimg = QImage(rgb8.data, w, h, rgb8.strides[0], fmt).copy()
                self._qimage = qimg
                return True

            # RGBA u otros → quedarnos con RGB para preview
            if c >= 3:
                rgb8 = y[..., :3]
                fmt = QImage.Format_RGB888
                qimg = QImage(rgb8.data, w, h, rgb8.strides[0], fmt).copy()
                self._qimage = qimg
                return True

            if c == 1:
                g = y[..., 0]
                rgb8 = np.repeat(g[..., None], 3, axis=2)
                fmt = QImage.Format_RGB888
                qimg = QImage(rgb8.data, w, h, rgb8.strides[0], fmt).copy()
                self._qimage = qimg
                return True

        # Si llegamos aquí, no generamos preview, pero la carga “maestra” fue correcta
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

