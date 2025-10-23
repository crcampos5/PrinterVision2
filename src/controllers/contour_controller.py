# contour_controller.py
from __future__ import annotations

from typing import List, Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QGraphicsScene

from views.scene_items.contour_item import ContourItem


class ContourController(QObject):
    """
    Detecta contornos desde el background del ScanTableController
    y gestiona sus ContourItem en la escena.
    Mantener simple: sin hilos, sin estados extra.
    """

    def __init__(self, scene: Optional[QGraphicsScene] = None, parent=None) -> None:
        super().__init__(parent)
        self._scene: Optional[QGraphicsScene] = scene
        self._items: List[ContourItem] = []
        self._min_area: float = 40000.0  # píxeles^2; ajustable si se necesita

    # --- Wiring desde MainWindow ---
    def attach_to_scene(self, scene: Optional[QGraphicsScene]) -> None:
        self.clear()
        self._scene = scene

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
        image = self._get_background_np(scan_ctrl)
        if image is None:
            self.clear()
            return
        items = self._detect_to_items(image)
        self._rebuild_items(items)

    def _get_background_np(self, scan_ctrl) -> Optional[np.ndarray]:
        # Preferir un método público si existe
        getter = getattr(scan_ctrl, "background_np", None)
        if callable(getter):
            return getter()
        # Fallback: acceder al modelo si es necesario
        model = getattr(scan_ctrl, "_model", None)
        return getattr(model, "scan_table_image", None) if model is not None else None

    # --- Detección y construcción de items ---
    def _detect_to_items(self, image: np.ndarray) -> List[ContourItem]:
        if image.ndim == 3 and image.shape[2] >= 3:
            gray = cv2.cvtColor(image[..., :3], cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Asegurar objetos en blanco
        white = int(np.count_nonzero(thr)); black = thr.size - white
        if white > black:
            thr = cv2.bitwise_not(thr)

        cnts, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = [c for c in cnts if cv2.contourArea(c) >= self._min_area]
        items: List[ContourItem] = []
        for c in cnts:
            # Se asume que ContourItem expone un helper de construcción desde cv-contour
            it = ContourItem.from_cv_contour(c)
            it.controller = self
            it.setZValue(10.0)  # por encima del background
            items.append(it)
        return items

    # --- Gestión simple de items en escena ---
    def _rebuild_items(self, new_items: List[ContourItem]) -> None:
        self.clear()
        if self._scene is None:
            return
        for it in new_items:
            self._scene.addItem(it)
            self._items.append(it)

    def clear(self) -> None:
        if self._scene is not None:
            for it in self._items:
                if it.scene() is self._scene:
                    self._scene.removeItem(it)
        self._items.clear()

    def on_selection_changed(self, item: ContourItem) -> None:
        if item.isSelected():
            rot = item.rotation()
            p_parent = item.pos()           # pos en coordenadas del padre
            p_scene  = item.scenePos()      # pos del (0,0) local en escena
            c_scene  = item.mapToScene(item.boundingRect().center())  # centro en escena
            angle = item.model.angle_o
            dic = item.model.direccion
           

    # --- API mínima pública ---
    def items(self) -> List[ContourItem]:
        return list(self._items)
