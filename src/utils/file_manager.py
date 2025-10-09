# file_manager.py
"""Utility helpers to centralize image loading operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Any, Dict, Tuple

import cv2
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


def load_scan_table(path: Path) -> np.ndarray:
    if not path.exists():
        return None

    try:       
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is not None and image.ndim == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    except Exception:
        return None

    if image is None:
        return None

    array = np.asarray(image)

    # Si viene en 2D (gris), opcionalmente añade eje de canal para coherencia (H, W, 1).
    # Esto NO cambia la información ni el dtype.
    if array.ndim == 2:
        array = array[..., np.newaxis]

    

    return array
    
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

def to_rgba8_preview(
    pixels: np.ndarray,
    photometric: Optional[str],
    cmyk_order: Optional[Tuple[int, int, int, int]],
    alpha_index: Optional[int],
) -> Optional[np.ndarray]:
    """
    Convierte un arreglo de imagen (cualquier dtype) a RGBA8 para previsualización.
    - Preserva alpha si alpha_index es válido.
    - Soporta CMYK (photometric='separated') con orden dado por cmyk_order.
    - No modifica `pixels`; retorna un nuevo np.ndarray (H, W, 4) dtype=uint8.
    """
    if pixels is None or pixels.size == 0:
        return None
    arr = np.asarray(pixels)
    if arr.ndim == 2:
        # Gris → RGB + A=255
        g = _to_u8(arr)
        a = np.full_like(g, 255, dtype=np.uint8)
        return np.ascontiguousarray(np.dstack([g, g, g, a]))

    if arr.ndim != 3:
        return None

    h, w, c = arr.shape
    # Alpha
    has_alpha = alpha_index is not None and 0 <= alpha_index < c
    A = _to_u8(arr[..., alpha_index]) if has_alpha else np.full((h, w), 255, dtype=np.uint8)

    # CMYK → RGB
    if (photometric or "").lower() == "separated" and c >= 4:
        order = cmyk_order if cmyk_order else (0, 1, 2, 3)
        C = _to_u8(arr[..., order[0]]).astype(np.float32) / 255.0
        M = _to_u8(arr[..., order[1]]).astype(np.float32) / 255.0
        Y = _to_u8(arr[..., order[2]]).astype(np.float32) / 255.0
        K = _to_u8(arr[..., order[3]]).astype(np.float32) / 255.0
        R = (1.0 - np.minimum(1.0, C + K))
        G = (1.0 - np.minimum(1.0, M + K))
        B = (1.0 - np.minimum(1.0, Y + K))
        R8 = (R * 255.0).round().astype(np.uint8)
        G8 = (G * 255.0).round().astype(np.uint8)
        B8 = (B * 255.0).round().astype(np.uint8)
        return np.ascontiguousarray(np.dstack([R8, G8, B8, A]))

    # RGB / RGBA / Gray+Alpha u otros
    if c >= 3:
        R = _to_u8(arr[..., 0])
        G = _to_u8(arr[..., 1])
        B = _to_u8(arr[..., 2])
        # Si no se indicó alpha_index pero hay 4º canal, úsalo como alpha de cortesía
        if not has_alpha and c >= 4:
            A = _to_u8(arr[..., 3])
        return np.ascontiguousarray(np.dstack([R, G, B, A]))

    if c == 2:
        # Asumimos [Gray, Alpha] si no se especifica
        if has_alpha:
            gray_chan = 1 - int(alpha_index == 0)  # si alpha es 0, gris es 1; si alpha es 1, gris es 0
        else:
            gray_chan = 0
        GY = _to_u8(arr[..., gray_chan])
        return np.ascontiguousarray(np.dstack([GY, GY, GY, A]))

    if c == 1:
        GY = _to_u8(arr[..., 0])
        return np.ascontiguousarray(np.dstack([GY, GY, GY, A]))

    return None

def save_result(
    path: Path,
    image: np.ndarray,
    photometric: str | None = None,
    dpi_x: float | None = None,
    dpi_y: float | None = None,
    icc_profile: bytes | None = None,
    ink_names: list[str] | None = None,
    extrasamples: list[int] | None = None,
    number_of_inks: int | None = None,
    inkset: int | None = None,  # 1 = CMYK
) -> bool:
    try:
        kws = {
            "append": False,     # <- NO anexar páginas
            "bigtiff": False,    # opcional
            "imagej": False,     # opcional
        }
        if photometric:
            kws["photometric"] = photometric  # 'rgb' | 'minisblack' | 'separated'
        if dpi_x and dpi_y:
            kws["resolution"] = (float(dpi_x), float(dpi_y))
            kws["resolutionunit"] = "INCH"
        if icc_profile:
            kws["iccprofile"] = icc_profile

        extratags = []
        # InkNames (id 333), NumberOfInks (id 334), InkSet (id 332)
        if ink_names:
            payload = ("\x00".join(ink_names) + "\x00").encode("latin1")
            extratags.append((333, "B", len(payload), payload, True))
        if number_of_inks is not None:
            extratags.append((334, "H", 1, number_of_inks, True))
        if inkset is not None:
            extratags.append((332, "H", 1, inkset, True))
        # ExtraSamples (id 338) SOLO si realmente es alfa
        if extrasamples:
            extratags.append((338, "H", len(extrasamples), extrasamples, True))
        if extratags:
            kws["extratags"] = extratags

        tifffile.imwrite(str(path), image, **kws)
        return True
    except Exception:
        return False

# --- Helpers internos mínimos (privados al módulo) ---

def _to_u8(ch: np.ndarray) -> np.ndarray:
    """
    Convierte un canal 2D a uint8 de forma robusta:
    - float: 0..1 → *255; >255 → clip a 0..65535 y /257; resto → normaliza min-max.
    - uint16: /257
    - uint8: retorna igual
    - otros enteros: normaliza min-max
    """
    ch = np.asarray(ch)
    if ch.dtype == np.uint8:
        return ch
    if ch.dtype == np.uint16:
        return (ch / 257.0).round().astype(np.uint8)
    if ch.dtype.kind == "f":
        x = np.nan_to_num(ch.astype(np.float32, copy=False))
        if x.size == 0:
            return np.zeros_like(x, dtype=np.uint8)
        xmax = float(np.max(x))
        xmin = float(np.min(x))
        if xmax <= 1.05 and xmin >= 0.0:
            x = np.clip(x, 0.0, 1.0) * 255.0
            return x.round().astype(np.uint8)
        if xmax > 255.0:
            x = np.clip(x, 0.0, 65535.0) / 257.0
            return x.round().astype(np.uint8)
        rng = xmax - xmin
        if rng <= 0.0:
            return np.zeros_like(x, dtype=np.uint8)
        x = (x - xmin) * (255.0 / rng)
        return x.round().astype(np.uint8)
    # otros enteros (incl. int16, int32, uint32…): normaliza min-max
    x = ch.astype(np.float32)
    if x.size == 0:
        return np.zeros_like(x, dtype=np.uint8)
    xmax = float(np.max(x))
    xmin = float(np.min(x))
    rng = xmax - xmin
    if rng <= 0.0:
        return np.zeros_like(x, dtype=np.uint8)
    x = (x - xmin) * (255.0 / rng)
    return x.round().astype(np.uint8)