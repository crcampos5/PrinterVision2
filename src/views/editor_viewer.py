"""Interactive image viewer widget with pan/zoom/rotate support."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent, QPixmap, QPainter
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

from utils.qt import numpy_to_qpixmap


class EditorViewer(QGraphicsView):
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
        
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)
        event.accept()

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
    
    def _refresh_view(self) -> None:
        if self.document.has_output:
            image = self.document.get_output_preview()
            pix = numpy_to_qpixmap(
                image,
                photometric_hint=getattr(self.document, "tile_photometric", None),
                cmyk_order=getattr(self.document, "tile_cmyk_order", None),
                alpha_index=getattr(self.document, "tile_alpha_index", None),
            )
            self.set_pixmap(pix)
        else:
            image = self.document.get_reference_preview()
            if image is not None:
                # referencia (JPG) no necesita hints
                self.set_pixmap(numpy_to_qpixmap(image))
            else:
                self.clear()
