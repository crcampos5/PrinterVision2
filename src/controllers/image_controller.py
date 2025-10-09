# image_controller.py
"""Controller coordinating ImageItem updates with ImageModel (QImage preview)."""

from __future__ import annotations
from pathlib import Path
from typing import List
import cv2
import numpy as np
from shiboken6 import isValid
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from controllers.scan_table_controller import ScanTableController
from models.image_model import ImageModel
from utils.file_manager import save_result
from views.scene_items import ImageItem


class ImageController(QObject):
    """Mediator between the ImageModel (QImage preview) and the scene ImageItem."""
    state_changed = Signal()

    def __init__(self, parent: QObject, ctrl_table: ScanTableController | None = None) -> None:
        super().__init__(parent)
        self._model = ImageModel()
        self._item = ImageItem()
        self._item.controller = self
        self.ctrl_table = ctrl_table
        self._scene: QGraphicsScene | None = None
        self._images: List[ImageItem] = []
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
    
    @property
    def has_output(self) -> bool:
        item_ok = False

        if (self._item is not None) and isValid(self._item):
            item_ok = True

            pixmap = getattr(self._item, "_pixmap", None)
            if isinstance(pixmap, QPixmap) and not pixmap.isNull():
                item_ok = True

        images_ok = any(
            (isValid(img) and getattr(img, "_pixmap", None) is not None and not getattr(img, "_pixmap").isNull())
            for img in self._images
        )

        return item_ok or images_ok
    
    def on_selection_changed(self) -> None:
        if self._item.isSelected():
            rot = self._item.rotation()
            p_parent = self._item.pos()           # pos en coordenadas del padre
            p_scene  = self._item.scenePos()      # pos del (0,0) local en escena
            c_scene  = self._item.mapToScene(self._item.boundingRect().center())  # centro en escena


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
        self._item.setPos(0,0)
        self._sync_item_from_model()
        if self._scene is not None and self._item.scene() is None and self._model.has_image():
            self._scene.addItem(self._item)
        self.state_changed.emit()
        return ok
    
    def connect_scan_table(self, scan_ctrl) -> None:
        """
        Conectar a la señal state_changed de ScanTableController.
        scan_ctrl debe exponer background_np() o un atributo ._model.scan_table_image
        """
        scan_ctrl.state_changed.connect(lambda: self._on_scan_table_changed(scan_ctrl))

    # --- Reacción ante cambios del background ---
    def _on_scan_table_changed(self, scan_ctrl) -> None:
        if self._scene is None:
            return
        self.clear()
        

    def clear(self) -> None:
        self._model.clear()
        self._item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self._item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self._item.set_image_pixmap(None)
        sc = self._item.scene()
        if sc is not None:
            sc.removeItem(self._item)
            for it in self._images:
                if it.scene() is sc:
                    sc.removeItem(it)
        self._images.clear()          
        self.state_changed.emit()

    def refresh(self) -> None:
        self._sync_item_from_model()

    def _sync_item_from_model(self) -> None:
        """Push model's QImage preview into the view item (as pixmap for painting)."""
        qimg = self._model.qimage
        self._item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self._item.setFlag(QGraphicsItem.ItemIsMovable, True)
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
    
    def save_output(self, path: Path) -> bool:

        img = self.generate_output()
        dpi_x = self._model.dpi_x
        dpi_y = self._model.dpi_y
#
        #dtype = img.dtype
        #channels = (img.shape[2] if img.ndim == 3 else 1)
#
        #width_px = self.ctrl_table._model.workspace_width_mm * dpi_x / 25.4
        #height_px = self.ctrl_table._model.workspace_height_mm * dpi_y / 25.4
        #white = 0
        #canvas = (np.full((height_px, width_px, channels), white, dtype=dtype)
        #        if channels > 1 else np.full((height_px, width_px), white, dtype=dtype))

        # Photometric según canales
        if img.ndim == 2 or (img.ndim == 3 and img.shape[2] == 1):
            photometric = "minisblack"
        elif img.ndim == 3 and img.shape[2] == 3:
            photometric = "rgb"
        elif img.ndim == 3 and img.shape[2] >= 4:
            photometric = "separated"  # CMYK (+ posibles spots)
        else:
            photometric = None

        # Metadatos heredados del tile
        icc = getattr(self, "tile_icc_profile", None)
        ink_names = getattr(self, "tile_ink_names", None)

        # Decidir si hay ALFA o si el 5º canal es SPOT:
        extrasamples = None
        number_of_inks = None
        inkset = None  # 1 = CMYK

        channels = img.shape[2] if (img.ndim == 3) else 1
        if photometric == "separated":
            # Si el tile traía alfa y sigue estando al final -> marcar ExtraSamples=ALPHA
            if self._model.alpha_index is not None and channels == (self._model.alpha_index + 1):
                extrasamples = [2]  # 2 = Unassociated Alpha
                # Si hay nombres de tintas y además alfa, no cuentes el alfa como 'ink'
                if ink_names:
                    ink_names = [n for i, n in enumerate(ink_names) if i != self._model.alpha_index]
            else:
                # No hay alfa: si hay nombres de tintas (p.ej. CMYK+Spot), declara el número de tintas
                if ink_names and len(ink_names) == channels:
                    number_of_inks = channels
                    inkset = 1  # CMYK base

        return save_result(
            path,
            img,
            photometric=photometric,
            dpi_x=dpi_x,
            dpi_y=dpi_y,
            icc_profile=icc,
            ink_names=ink_names,
            extrasamples=extrasamples,
            number_of_inks=number_of_inks,
            inkset=inkset,
        )
    
    def generate_output(self) -> np.ndarray:

        img = self._model.pixels
        dpi_x = self._model.dpi_x
        dpi_y = self._model.dpi_y

        dtype = img.dtype
        channels = (img.shape[2] if img.ndim == 3 else 1)

        width_px = int(round(self.ctrl_table._model.workspace_width_mm * dpi_x / 25.4))
        height_px = int(round(self.ctrl_table._model.workspace_height_mm * dpi_y / 25.4))
        white = 0
        canvas = (np.full((height_px, width_px, channels), white, dtype=dtype)
                if channels > 1 else np.full((height_px, width_px), white, dtype=dtype))
        
        for item in self._images:
            center_scene = item.mapToScene(item.boundingRect().center())
            csx, csy = center_scene.x(), center_scene.y()

            pos_x = csx / self._model.scale_sx
            pos_y = csy / self._model.scale_sy

            rot_final = item.rotation()

            # Ajusta canales para compatibilidad con canvas (permitimos 1 canal extra como alpha)
            ch = img.shape[2]
            if ch < channels:
                img = np.concatenate([img, np.repeat(img[..., -1:], channels - ch, axis=2)], axis=2)
                ch = channels
            if ch > channels + 1:
                img = img[..., :channels + 1]
                ch = img.shape[2]

            h, w = img.shape[:2]

            M = cv2.getRotationMatrix2D((pos_x, pos_y), rot_final, 1)
            cos = abs(M[0, 0]); sin = abs(M[0, 1])
            new_w = int(round((h * sin) + (w * cos)))
            new_h = int(round((h * cos) + (w * sin)))

            M[0, 2] += (new_w / 2.0) - pos_x
            M[1, 2] += (new_h / 2.0) - pos_y

            if ch <= 4:
                border_val = (white,) * ch
            else:
                border_val = white

            warped = cv2.warpAffine(img, M, (new_w, new_h), flags=cv2.INTER_NEAREST, borderValue=border_val)

            x0 = int(round(pos_x - new_w / 2.0))
            y0 = int(round(pos_y - new_h / 2.0))

            if x0 >= canvas.shape[1] or y0 >= canvas.shape[0] or (x0 + new_w <= 0) or (y0 + new_h <= 0):
                continue

            xs = max(0, -x0); ys = max(0, -y0)
            x0 = max(0, x0); y0 = max(0, y0)
            x1 = min(x0 + new_w - xs, canvas.shape[1])
            y1 = min(y0 + new_h - ys, canvas.shape[0])
            if x1 <= x0 or y1 <= y0:
                continue

            tile_slice = warped[ys:ys + (y1 - y0), xs:xs + (x1 - x0)]
            region = canvas[y0:y1, x0:x1]

             # Máscara: alpha extra si canales = canvas+1, si no ≠ white
            has_extra_alpha = (tile_slice.ndim == 3 and tile_slice.shape[2] == (channels + 1))
            if has_extra_alpha:
                alpha = tile_slice[..., -1]
                color = tile_slice[..., :channels]
                mask = (alpha > 0)
                region[mask] = color[mask]
            else:
                if tile_slice.ndim == 3:
                    # Ajuste de canales por seguridad
                    if tile_slice.shape[2] > channels:
                        tile_slice = tile_slice[..., :channels]
                    elif tile_slice.shape[2] < channels:
                        tile_slice = np.concatenate(
                            [tile_slice, np.repeat(tile_slice[..., -1:], channels - tile_slice.shape[2], axis=2)], axis=2
                        )
                    mask = np.any(tile_slice != white, axis=2)
                    region[mask] = tile_slice[mask]
                else:
                    mask = (tile_slice != white)
                    region[mask] = tile_slice[mask]

            canvas[y0:y1, x0:x1] = region

        return canvas
