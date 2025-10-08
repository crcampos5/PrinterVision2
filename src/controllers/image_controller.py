# image_controller.py
"""Controller coordinating ImageItem updates with ImageModel (QImage preview)."""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import QGraphicsScene

from models.image_model import ImageModel
from views.scene_items import ImageItem


class ImageController(QObject):
    """Mediator between the ImageModel (QImage preview) and the scene ImageItem."""
    state_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = ImageModel()
        self._item = ImageItem()
        self._item.controller = self
        self._scene: QGraphicsScene | None = None

        self._item.setZValue(100.0)
        self._target_mmpp_x: float | None = None
        self._target_mmpp_y: float | None = None
        self._sync_item_from_model()

    @property
    def item(self) -> ImageItem:
        return self._item

    @property
    def model(self) -> ImageModel:
        return self._model
    
    def on_selection_changed(self) -> None:
        if self._item.isSelected():
            rot = self._item.rotation()
            p_parent = self._item.pos()           # pos en coordenadas del padre
            p_scene  = self._item.scenePos()      # pos del (0,0) local en escena
            c_scene  = self._item.mapToScene(self._item.boundingRect().center())  # centro en escena

            print(f"Rotación: {rot:.2f}°")
            print(f"Posición (parent): x={p_parent.x():.3f}, y={p_parent.y():.3f}")
            print(f"Posición (scene 0,0): x={p_scene.x():.3f}, y={p_scene.y():.3f}")
            print(f"Centro (scene): x={c_scene.x():.3f}, y={c_scene.y():.3f}")


    def attach_to_scene(self, scene: QGraphicsScene | None) -> None:
        if self._scene is scene:
            return
        old = self._item.scene()
        if old is not None and old is not scene:
            old.removeItem(self._item)
        self._scene = scene
        if scene is not None and self._item.scene() is not scene:
            scene.addItem(self._item)
            self._sync_item_from_model()

    def load_image(self, path: Path) -> bool:
        ok = self._model.load_image(path)
        self._sync_item_from_model()
        if self._scene is not None and self._item.scene() is None and self._model.has_image():
            self._scene.addItem(self._item)
        self.state_changed.emit()
        return ok

    def clear(self) -> None:
        self._model.clear()
        self._item.set_image_pixmap(None)
        sc = self._item.scene()
        if sc is not None:
            sc.removeItem(self._item)
        self.state_changed.emit()

    def refresh(self) -> None:
        self._sync_item_from_model()

    def _sync_item_from_model(self) -> None:
        """Push model's QImage preview into the view item (as pixmap for painting)."""
        qimg = self._model.qimage
        if qimg is None or qimg.isNull():
            self._item.set_image_pixmap(None)
            return
        self._item.set_image_pixmap(QPixmap.fromImage(qimg))
        self._apply_physical_scale()

    def set_target_mm_per_pixel(self, mmpp_x: float | None, mmpp_y: float | None) -> None:
        self._target_mmpp_x = mmpp_x
        self._target_mmpp_y = mmpp_y
        self._apply_physical_scale()
    
    def _apply_physical_scale(self) -> None:
        """Escala no uniforme para que la imagen respete mm por píxel del scan_table."""
        if self._target_mmpp_x is None or self._target_mmpp_y is None:
            return
        qimg = self._model.qimage
        if qimg is None or qimg.isNull():
            return
        w_px, h_px = qimg.width(), qimg.height()
        width_mm, height_mm = self._model.width_mm, self._model.height_mm
        if not width_mm or not height_mm or w_px <= 0 or h_px <= 0:
            return

        mmpp_img_x = width_mm / float(w_px)
        mmpp_img_y = height_mm / float(h_px)

        self._model.scale_sx = mmpp_img_x / float(self._target_mmpp_x)
        self._model.scale_sy = mmpp_img_y / float(self._target_mmpp_y)

        # Reemplaza cualquier transform previa con la escala física
        self._item.setTransform(QTransform().scale(self._model.scale_sx, self._model.scale_sy), False)
