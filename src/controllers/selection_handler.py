from __future__ import annotations

from typing import Optional
from PySide6.QtCore import QObject, Signal, QEvent, Qt
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

class SelectionHandler(QObject):
    selection_changed = Signal()

    def __init__(self, scan_table_item: QGraphicsItem, image_item: QGraphicsItem, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._scene: Optional[QGraphicsScene] = None
        self._bg = scan_table_item
        self._img = image_item

    def attach_to_scene(self, scene: QGraphicsScene | None) -> None:
        if self._scene is scene:
            return
        if self._scene is not None:
            try:
                self._scene.removeEventFilter(self)
                self._scene.selectionChanged.disconnect(self._on_sel)
            except Exception:
                pass
        self._scene = scene
        if scene is None:
            return
        # Flags básicos
        self._bg.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self._bg.setFlag(QGraphicsItem.ItemIsMovable, False)
        self._img.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self._img.setFlag(QGraphicsItem.ItemIsMovable, True)
        # Eventos básicos
        scene.installEventFilter(self)
        scene.selectionChanged.connect(self._on_sel)

    def _on_sel(self) -> None:
        self.selection_changed.emit()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # solo lo mínimo
        return False
