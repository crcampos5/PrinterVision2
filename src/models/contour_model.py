from __future__ import annotations

from typing import Any
import cv2
import numpy as np
from PySide6.QtGui import QPolygonF
from PySide6.QtCore import QPointF


class ContourModel:
    """Datos básicos de un contorno detectado."""

    def __init__(
        self,
        original_contour: Any | None = None,
        scene_contour: QPolygonF | None = None,
        scene_box: QPolygonF | None = None,
    ) -> None:
        self.original_contour = original_contour
        self.scene_contour = QPolygonF(scene_contour) if scene_contour is not None else QPolygonF()
        self.scene_box = QPolygonF(scene_box) if scene_box is not None else QPolygonF()
        self.cx_o = None
        self.cy_o = None
        self.w_o = None
        self.h_o = None
        self.angle_o = None
        self.direccion = None
        self.calc_data()

    def set_original_contour(self, contour: Any) -> None:
        self.original_contour = contour

    def set_scene_contour(self, polygon: QPolygonF) -> None:
        self.scene_contour = QPolygonF(polygon)

    def set_scene_box(self, polygon: QPolygonF) -> None:
        self.scene_box = QPolygonF(polygon)
    
    def calc_data(self) -> None:
        points_list = [[point.x(), point.y()] for point in self.scene_contour]
        points_np = np.array(points_list, dtype=np.float32)
        rect = cv2.minAreaRect(points_np)
        (self.cx_o, self.cy_o), (self.w_o, self.h_o), self.angle_o = rect
        box_points = cv2.boxPoints(rect)
        
        # Calcular distancias
        distancia01 = cv2.norm(box_points[1] - box_points[0])
        distancia03 = cv2.norm(box_points[3] - box_points[0])
        
        # Determinar el lado largo y crear el polígono
        if distancia01 < distancia03:
            self.angle_o += 90
        
        
        # Crear polígono una sola vez
        poly = QPolygonF([QPointF(float(x), float(y)) for x, y in box_points])
        self.scene_box = poly
        
        ang = np.deg2rad(-self.angle_o)
        R = np.array([[np.cos(ang), -np.sin(ang)],
                    [np.sin(ang),  np.cos(ang)]])
        pts = np.asarray(points_np, dtype=float) - (self.cx_o, self.cy_o)
        pts_rot = pts @ R.T + (self.cx_o, self.cy_o)

        #poly = QPolygonF([QPointF(float(x), float(y)) for x, y in pts_rot])
        #self.scene_box = poly

        pts_rot = np.floor(pts_rot).astype(int)

        peri = cv2.arcLength(pts_rot, True)
        epsilon = 0.01 * peri
        pts_rot = cv2.approxPolyDP(pts_rot, epsilon, True)
        pts_rot = pts_rot.reshape(-1, 2)
        #poly = QPolygonF([QPointF(float(x), float(y)) for x, y in pts_rot])
        #self.scene_box = poly
        y_min, y_max = np.min(pts_rot[:,1]), np.max(pts_rot[:,1])
        y0 = (y_max + y_min)/2


        x, y, w, h = cv2.boundingRect(pts_rot)
        pts_shift = pts_rot - np.array([x, y])

        mask = np.zeros((h, w), np.uint8)
        cv2.fillPoly(mask, [pts_shift], 255)

        # Índice de corte relativo a la máscara
        idx = int(round(y0 - y))
        idx = np.clip(idx, 0, h)  # limitar dentro de la máscara

        arriba = np.count_nonzero(mask[:idx, :]) * 1.0
        abajo = np.count_nonzero(mask[idx:, :]) * 1.0

        if arriba > abajo:
            self.direccion = "abajo"
            self.angle_o += 180
        else: 
            self.direccion = "arriba"