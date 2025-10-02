"""Utility helpers to centralize image loading operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .io import load_image_data

if TYPE_CHECKING:  # pragma: no cover - imported for type checkers only
    from .io import ImageData


def load_reference_image(path: Path) -> Optional["ImageData"]:
    """Load the reference image from ``path``.

    This helper is a thin wrapper around :func:`load_image_data` that exists to
    provide a semantic entry point for higher level components. Keeping the
    logic centralized makes it easier to evolve the loading behaviour (e.g.
    logging, validation) without touching every call site.
    """

    return load_image_data(path)


def load_tile_image(path: Path) -> Optional["ImageData"]:
    """Load a mosaic/tile image from ``path``.

    The behaviour mirrors :func:`load_reference_image`, but the dedicated
    function allows us to later specialise how tile assets are handled without
    changing the public API of the rest of the application.
    """

    return load_image_data(path)
