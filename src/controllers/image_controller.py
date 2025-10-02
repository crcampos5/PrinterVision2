"""Controller coordinating :class:`ImageItem` updates with :class:`ImageModel`."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsScene

from models.image_model import ImageModel
from views.scene_items import ImageItem


class ImageController(QObject):
    """High level helper acting as mediator between model and scene item."""

    state_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = ImageModel()
        self._item = ImageItem()
        self._scene: QGraphicsScene | None = None
        pixmap = self._model.pixmap
        if pixmap is not None and not pixmap.isNull():
            self._item.setPixmap(pixmap)

    @property
    def item(self) -> ImageItem:
        """Return the underlying :class:`ImageItem` used for display."""

        return self._item

    @property
    def model(self) -> ImageModel:
        """Expose the backing model for read-only operations."""

        return self._model

    def attach_to_scene(self, scene: QGraphicsScene | None) -> None:
        """Attach the image item to ``scene`` keeping references in sync."""

        if self._scene is scene:
            return
        current_scene = self._item.scene()
        if current_scene is not None and current_scene is not scene:
            current_scene.removeItem(self._item)
        self._scene = scene
        if scene is not None and self._item.scene() is not scene:
            scene.addItem(self._item)
            self._sync_item_from_model()

    def load_image(self, path: Path) -> bool:
        """Load an image from ``path`` and update the scene item."""

        if not self._model.load_image(path):
            return False
        self._sync_item_from_model()
        if self._scene is not None and self._item.scene() is None:
            self._scene.addItem(self._item)
        self.state_changed.emit()
        return True

    def set_pixmap(self, pixmap: QPixmap | None, path: Path | None = None) -> None:
        """Assign a pixmap directly, bypassing on-disk loading."""

        self._model.set_pixmap(pixmap, path)
        self._sync_item_from_model()
        if self._scene is not None and self._item.scene() is None and self._model.has_image():
            self._scene.addItem(self._item)
        self.state_changed.emit()

    def clear(self) -> None:
        """Clear the current pixmap from both model and scene."""

        self._model.clear()
        self._item.setPixmap(QPixmap())
        current_scene = self._item.scene()
        if current_scene is not None:
            current_scene.removeItem(self._item)
        self.state_changed.emit()

    def refresh(self) -> None:
        """Re-synchronise the item from the current model state."""

        self._sync_item_from_model()

    def _sync_item_from_model(self) -> None:
        pixmap = self._model.pixmap
        if pixmap is None or pixmap.isNull():
            self._item.setPixmap(QPixmap())
            current_scene = self._item.scene()
            if current_scene is not None:
                current_scene.removeItem(self._item)
            return
        self._item.setPixmap(pixmap)
