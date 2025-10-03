from __future__ import annotations

from PySide6.QtGui import QPolygonF

from models.contour_model import ContourModel


class ContourItem(QPolygonF):
    """Representación gráfica simple de un contorno."""

    def __init__(self, model: ContourModel) -> None:
        super().__init__(model.scene_contour)
        self.model = model

    def sync_from_model(self) -> None:
        self.swap(QPolygonF(self.model.scene_contour))
