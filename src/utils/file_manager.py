# file_manager.py
"""Utility helpers to centralize image loading operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Any, Dict

import numpy as np
import tifffile

from .io import (
    _rational_to_float,
    _apply_resolution_unit,
    _compute_size_mm,
)
from .io import load_image_data  # existente, no se toca

if TYPE_CHECKING:  # pragma: no cover
    from .io import ImageData


def load_reference_image(path: Path) -> Optional["ImageData"]:
    return load_image_data(path)


def load_tile_image(path: Path) -> Optional["ImageData"]:
    return load_image_data(path)


def load_tif(path: Path) -> Optional[Dict[str, Any]]:
    """
    Carga un TIF y retorna un dict con:
      - pixels: np.ndarray (H, W, C) o (H, W, 1) si era gris
      - dpi_x, dpi_y: float|None
      - width_mm, height_mm: float|None
      - photometric: str|None
      - cmyk_order: tuple|None  (índices C,M,Y,K)
      - alpha_index: int|None
      - icc_profile: bytes|None
      - ink_names: list[str]|None
    NOTA: No retorna ImageData; deja la estructura “plana” para usar en el modelo.
    """
    if not path.exists() or path.suffix.lower() != ".tif":
        return None

    try:
        with tifffile.TiffFile(str(path)) as tif:
            page = tif.pages[0]
            image = page.asarray()
            tags = page.tags

            photometric = (page.photometric.name.lower() if page.photometric else None)
            extras = list(page.extrasamples) if page.extrasamples is not None else []
            alpha_index = None

            # ICC profile
            icc = None
            icc_tag = tags.get("ICCProfile")
            if icc_tag is not None:
                icc = icc_tag.value  # bytes

            # InkNames / orden de CMYK
            ink_names = None
            cmyk_order = None
            inknames_tag = tags.get("InkNames")
            if photometric == "separated":
                if inknames_tag is not None:
                    raw = inknames_tag.value
                    if isinstance(raw, (bytes, bytearray)):
                        ink_names = [n for n in raw.decode("latin1").split("\x00") if n]
                    elif isinstance(raw, str):
                        ink_names = [n for n in raw.split("\x00") if n]
                if ink_names:
                    def idx_of(tgt: str):
                        for i, n in enumerate(ink_names):
                            nn = n.strip().lower()
                            if tgt in nn:
                                return i
                        return None
                    iC, iM, iY = idx_of("cyan"), idx_of("magenta"), idx_of("yellow")
                    iK = idx_of("black") or idx_of("key")
                    if None not in (iC, iM, iY, iK):
                        cmyk_order = (iC, iM, iY, iK)
                if extras:
                    alpha_index = image.shape[2] - 1

            # DPI
            unit_tag = tags.get("ResolutionUnit")
            unit_code = int(unit_tag.value) if unit_tag else None
            x_res_tag = tags.get("XResolution")
            y_res_tag = tags.get("YResolution")

            dpi_x = _apply_resolution_unit(
                _rational_to_float(x_res_tag.value if x_res_tag else None),
                unit_code,
            )
            dpi_y = _apply_resolution_unit(
                _rational_to_float(y_res_tag.value if y_res_tag else None),
                unit_code,
            )
    except Exception:
        return None

    arr = np.asarray(image)
    if arr.ndim == 2:
        arr = arr[..., np.newaxis]

    width_mm, height_mm = _compute_size_mm(arr.shape[:2], dpi_x, dpi_y)

    return {
        "pixels": arr,
        "dpi_x": dpi_x,
        "dpi_y": dpi_y,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "photometric": photometric,
        "cmyk_order": cmyk_order,
        "alpha_index": alpha_index,
        "icc_profile": icc,
        "ink_names": ink_names,
    }
