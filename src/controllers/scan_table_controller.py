"""Controller orchestrating the scan table background between model and view."""

from __future__ import annotations

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsScene

from models.scan_table_model import PixmapSource, ScanTableModel
from views.scene_items import ScanTableItem


class ScanTableController:
    """High level controller coordinating the scan table background."""

    def __init__(self, model: ScanTableModel) -> None:
        self._model = model
        self._scene: QGraphicsScene | None = None
        self._item = ScanTableItem()
        # Sync the scene item with any pre-loaded background.
        pixmap = self._model.background_pixmap
        if pixmap is not None and not pixmap.isNull():
            self._item.set_background_pixmap(pixmap)

    @property
    def item(self) -> ScanTableItem:
        """Return the underlying graphics item used for display."""
        return self._item

    def attach_to_scene(self, scene: QGraphicsScene | None) -> None:
        """Attach the scan table background item to a graphics scene."""
        if self._scene is scene:
            return
        current_scene = self._item.scene()
        if current_scene is not None and current_scene is not scene:
            current_scene.removeItem(self._item)
        self._scene = scene
        if scene is not None and self._item.scene() is not scene:
            scene.addItem(self._item)
            self._sync_item_from_model()

    def load_background(self, source: PixmapSource) -> bool:
        """Load a background image and update the scene item."""
        if not self._model.load_background(source):
            return False
        pixmap = self._model.background_pixmap
        if pixmap is None:
            return False
        self._item.set_background_pixmap(pixmap)
        if self._scene is not None and self._item.scene() is None:
            self._scene.addItem(self._item)
        return True

    def clear_background(self) -> None:
        """Remove the background image from both model and scene."""
        self._model.clear_background()
        self._item.setPixmap(QPixmap())
        current_scene = self._item.scene()
        if current_scene is not None:
            current_scene.removeItem(self._item)

    def refresh(self) -> None:
        """Resynchronise the scene item with the current model state."""
        self._sync_item_from_model()

    def _sync_item_from_model(self) -> None:
        pixmap = self._model.background_pixmap
        if pixmap is None or pixmap.isNull():
            self._item.setPixmap(QPixmap())
            current_scene = self._item.scene()
            if current_scene is not None:
                current_scene.removeItem(self._item)
            return
        self._item.set_background_pixmap(pixmap)
        if self._scene is not None and self._item.scene() is None:
            self._scene.addItem(self._item)
