"""File-system helpers for image handling."""

from __future__ import annotations
from pathlib import Path
import sys
from typing import Optional

def _rational_to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        if isinstance(value, (tuple, list)) and len(value) == 2:
            num, den = value
            den = float(den)
            if den == 0:
                return None
            return float(num) / den
        return float(value)
    except Exception:
        return None


def _apply_resolution_unit(resolution: Optional[float], unit_code: Optional[int]) -> Optional[float]:
    """Convert raw resolution to dots-per-inch taking the unit into account."""
    if resolution is None or resolution <= 0:
        return None
    if unit_code == 2:  # inch
        return resolution
    if unit_code == 3:  # centimeter
        return resolution * 2.54
    if unit_code == 1:  # no units
        return None
    return None


def _compute_size_mm(shape: tuple[int, ...], dpi_x: Optional[float], dpi_y: Optional[float]) -> tuple[Optional[float], Optional[float]]:
    height_px = shape[0]
    width_px = shape[1]
    width_mm = (width_px / dpi_x * 25.4) if dpi_x else None
    height_mm = (height_px / dpi_y * 25.4) if dpi_y else None
    return width_mm, height_mm

def resource_path(relative_path: str) -> Path:
    """Obtiene la ruta válida tanto en desarrollo como en ejecutable."""
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)
    return Path(base_path) / relative_path
