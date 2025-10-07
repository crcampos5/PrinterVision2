# contour_item.py
from __future__ import annotations
from PySide6.QtGui import QPolygonF, QPen
from PySide6.QtWidgets import QGraphicsPolygonItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from models.contour_model import ContourModel

class ContourItem(QGraphicsPolygonItem):
    """Item gráfico de un contorno."""
    def __init__(self, model: ContourModel) -> None:
        super().__init__(model.scene_contour)
        self.model = model
        self.controller = None
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsFocusable
        )
        self.setAcceptedMouseButtons(Qt.LeftButton)
        # Estilo por defecto
        self.setPen(QPen(Qt.red, 4, Qt.SolidLine))
        self.setBrush(Qt.NoBrush)

    def sync_from_model(self) -> None:
        self.setPolygon(QPolygonF(self.model.scene_contour))

    def on_selected(self):
        self.controller.on_selection_changed(self)

    @classmethod
    def from_cv_contour(cls, contour_np) -> "ContourItem":
        # contour_np: (N,1,2) o (N,2)
        import numpy as np
        pts = contour_np.reshape(-1, 2).astype(float)
        poly = QPolygonF([QPointF(float(x), float(y)) for x, y in pts])
        m = ContourModel(original_contour=contour_np, scene_contour=poly)
        return cls(m)
