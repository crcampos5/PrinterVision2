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
from views.scene_items.plantilla_item import PlantillaItem


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
    
    
    def has_output(self) -> bool:
        item_ok = False

        if (self._item is not None) and isValid(self._item):
            
            pixmap = self._item.pixmap()
            if isinstance(pixmap, QPixmap) and not pixmap.isNull():
                item_ok = True

        images_ok = any(
        (
            isValid(img)
            and isinstance(img.pixmap(), QPixmap)
            and not img.pixmap().isNull()
        )
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

    def delete_item(self, item):
        parent = item.parentItem()
        if parent is not None and isValid(parent) and isinstance(parent, PlantillaItem):
            plc_ctrl = getattr(parent, "controller", None)
            if plc_ctrl and hasattr(plc_ctrl, "delete_item"):
                plc_ctrl.delete_item(parent)
                return

        sc = item.scene()
        if sc is not None and item.scene() is sc:
            sc.removeItem(item)
        if item is self._item:
            
            self._model.clear()
            self._item = ImageItem()
            self._item.controller = self
            self._item.setZValue(100.0)
        else:
            try:
                self._images.remove(item)
            except ValueError:
                pass
        self.state_changed.emit()
        

    def clear(self) -> None:
        self._model.clear()

        # principal
        if self._item and isValid(self._item):
            if self._item.parentItem():
                self._item.setParentItem(None)
            sc0 = self._item.scene()
            if sc0 is not None:
                sc0.removeItem(self._item)
            self._item.set_image_pixmap(None)
            self._item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self._item.setFlag(QGraphicsItem.ItemIsMovable, True)

        # clones / imágenes adicionales
        for it in list(self._images):
            if not it or not isValid(it):
                continue
            if it.parentItem():
                it.setParentItem(None)
            sc_it = it.scene()
            if sc_it is not None:
                sc_it.removeItem(it)

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
        """
        Composición por superposición (MAX por canal):
        - Crea el canvas (mm -> px) según workspace y DPI.
        - Para cada item (self._item y self._images):
            * Calcula su centro en escena -> coordenadas de canvas.
            * Rota la imagen base expandiendo el lienzo para evitar cortes.
            * Pega al canvas usando composición por máximo por canal (no borra tinta previa).
        - Sin máscaras ni conversiones. Mantiene dtype y número de canales del modelo.
        """
        import cv2, math
        import numpy as np

        img = self._model.pixels  # H x W x C (CMYK o similar) o H x W
        if img is None:
            raise ValueError("ImageModel.pixels es None")

        # --- Canvas en píxeles (mm -> px) ---
        dpi_x = float(self._model.dpi_x)
        dpi_y = float(self._model.dpi_y)
        width_px  = int(round(self.ctrl_table._model.workspace_width_mm  * dpi_x / 25.4))
        height_px = int(round(self.ctrl_table._model.workspace_height_mm * dpi_y / 25.4))
        if width_px <= 0 or height_px <= 0:
            raise ValueError(f"Tamaño de canvas inválido: {width_px}x{height_px}")

        dtype = img.dtype
        if img.ndim == 3:
            channels = img.shape[2]
            canvas = np.zeros((height_px, width_px, channels), dtype=dtype)  # CMYK blanco = 0
        elif img.ndim == 2:
            canvas = np.zeros((height_px, width_px), dtype=dtype)
        else:
            raise ValueError(f"Forma de imagen no soportada: {img.shape}")

        Hc, Wc = canvas.shape[:2]
        Hi, Wi = img.shape[:2]

        # Centro de la imagen base (para rotación)
        cx_img = (Wi - 1) / 2.0
        cy_img = (Hi - 1) / 2.0

        # --- Lista de items: principal + clones (ignorando None) ---
        items = [x for x in ([getattr(self, "_item", None)] + list(getattr(self, "_images", []))) if x is not None]

        for item in items:
            # Centro del item en escena -> píxeles del canvas (usando escalas del modelo)
            center_scene = item.mapToScene(item.boundingRect().center())
            csx, csy = center_scene.x(), center_scene.y()
            pos_x = int(round(csx / self._model.scale_sx))
            pos_y = int(round(csy / self._model.scale_sy))

            # ----- ROTACIÓN expandida (evita recortes) -----
            angle_deg = float(item.rotation())
            M = cv2.getRotationMatrix2D((cx_img, cy_img), -angle_deg, 1.0)

            cos_a = abs(M[0, 0])
            sin_a = abs(M[0, 1])
            newW = int(math.ceil(Hi * sin_a + Wi * cos_a))
            newH = int(math.ceil(Hi * cos_a + Wi * sin_a))

            # Recentrar en el nuevo tamaño
            M[0, 2] += (newW / 2.0) - cx_img
            M[1, 2] += (newH / 2.0) - cy_img

            # Rotar canal por canal (soporta C>4)
            if img.ndim == 3:
                img_rot = np.zeros((newH, newW, img.shape[2]), dtype=img.dtype)
                for c in range(img.shape[2]):
                    img_rot[:, :, c] = cv2.warpAffine(
                        img[:, :, c], M, (newW, newH),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT,
                        borderValue=0  # 0 = sin tinta
                    )
            else:
                img_rot = cv2.warpAffine(
                    img, M, (newW, newH),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=0
                )

            # Tamaño del parche rotado
            Hi_r, Wi_r = img_rot.shape[:2]

            # ----- Posicionamiento centrado y clipping -----
            x0 = int(round(pos_x - Wi_r / 2))
            y0 = int(round(pos_y - Hi_r / 2))
            x1 = x0 + Wi_r
            y1 = y0 + Hi_r

            x0c = max(0, x0); y0c = max(0, y0)
            x1c = min(Wc, x1); y1c = min(Hc, y1)
            if x1c <= x0c or y1c <= y0c:
                continue  # Fuera del canvas

            ix0 = x0c - x0
            iy0 = y0c - y0
            ix1 = ix0 + (x1c - x0c)
            iy1 = iy0 + (y1c - y0c)

            # ----- Composición por máximo (superposición) -----
            dst = canvas[y0c:y1c, x0c:x1c]
            src = img_rot[iy0:iy1, ix0:ix1]

            # Alinear dimensiones para operar por canal
            if dst.ndim == 3 and src.ndim == 2:
                src = src[..., None]
            if dst.ndim == 3 and src.shape[2] < dst.shape[2]:
                # Mezcla solo los canales presentes en src
                dst_slice = dst[:, :, :src.shape[2]]
            else:
                dst_slice = dst

            # MAX por canal: evita que ceros del parche borren tinta previa
            np.maximum(dst_slice, src, out=dst_slice)

        return canvas

