from __future__ import annotations

from typing import Any

from PySide6.QtGui import QPolygonF


class ContourModel:
    """Datos básicos de un contorno detectado."""

    def __init__(
        self,
        original_contour: Any | None = None,
        scene_contour: QPolygonF | None = None,
        scene_box: QPolygonF | None = None,
    ) -> None:
        self.original_contour = original_contour
        self.scene_contour = QPolygonF(scene_contour) if scene_contour is not None else QPolygonF()
        self.scene_box = QPolygonF(scene_box) if scene_box is not None else QPolygonF()

    def set_original_contour(self, contour: Any) -> None:
        self.original_contour = contour

    def set_scene_contour(self, polygon: QPolygonF) -> None:
        self.scene_contour = QPolygonF(polygon)

    def set_scene_box(self, polygon: QPolygonF) -> None:
        self.scene_box = QPolygonF(polygon)
