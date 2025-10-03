from __future__ import annotations

from typing import List

from models.contour_model import ContourModel
from views.scene_items.contour_item import ContourItem


class ContourController:
    """Gestor mínimo para múltiples contornos."""

    def __init__(self) -> None:
        self._items: List[ContourItem] = []

    def create_item(self, model: ContourModel) -> ContourItem:
        item = ContourItem(model)
        self._items.append(item)
        return item

    def remove_item(self, item: ContourItem) -> None:
        if item in self._items:
            self._items.remove(item)

    def items(self) -> List[ContourItem]:
        return list(self._items)
