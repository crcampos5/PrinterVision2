"""Interactive image viewer widget with pan/zoom/rotate support."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent, QPixmap, QPainter
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


class ImageViewer(QGraphicsView):
    """QGraphicsView configured for smooth zooming, panning, and rotation."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item: QGraphicsPixmapItem | None = None

        self.setRenderHints(self.renderHints() | QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 (Qt naming)
        """Zoom or rotate depending on modifier keys."""
        if event.modifiers() & Qt.ControlModifier:
            angle = 5 if event.angleDelta().y() > 0 else -5
            self.rotate(angle)
            event.accept()
            return

        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Display a pixmap in the scene and fit it to view."""
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        self.reset_view()
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def clear(self) -> None:
        """Remove any image from the viewer."""
        self._scene.clear()
        self.resetTransform()
        self._pixmap_item = None

    def reset_view(self) -> None:
        """Reset transformations applied to the view."""
        self.resetTransform()
