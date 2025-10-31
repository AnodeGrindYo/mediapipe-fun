"""
Module de configuration de l'application.

Ce module définit une dataclass immuable `Config` qui centralise tous les
paramètres de l'application (détection/tracking, webcam, rendu, etc.).
L'immutabilité (frozen=True) sécurise la configuration : une fois créée,
elle ne peut plus être modifiée acciden­tellement en cours d'exécution.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """
    Conteneur immuable des paramètres de l'application.

    Remarques générales
    -------------------
    - `@dataclass(frozen=True)` génère automatiquement __init__, __repr__, __eq__, etc.,
      et rend les instances **immuables** (attributs en lecture seule).
      → Avantages : sécurité (pas de mutation involontaire), simplicité, hashabilité possible.

    Attributs
    ---------
    max_num_hands : int
        Nombre maximal de mains à détecter (borne supérieure de la détection).
    detection_confidence : float
        Seuil minimal de confiance pour considérer une détection comme valide.
    tracking_confidence : float
        Seuil minimal de confiance pour maintenir le suivi d'éléments déjà détectés.
    model_complexity : int
        Niveau de complexité du modèle de détection/suivi (compromis précision/latence).
    smooth_alpha : float
        Coefficient de lissage (EMA ou paramètres analogues) pour stabiliser les signaux.
    min_rect_size : int
        Taille minimale (en pixels) admise pour le rectangle ROI (filtre anti-bruit).
    camera_index : int
        Index de la caméra à ouvrir (0 = webcam par défaut).
    mirror_frame : bool
        Si True, applique un miroir horizontal à la frame (expérience plus "naturelle").
    draw_landmarks : bool
        Si True, permet (selon l'implémentation associée) d'afficher les points clés de la main.
    window_title : str
        Titre de la fenêtre OpenCV (identifiant d'affichage et de propriétés de fenêtre).
    """

    max_num_hands: int = 2
    detection_confidence: float = 0.6
    tracking_confidence: float = 0.5
    model_complexity: int = 1
    smooth_alpha: float = 0.4
    min_rect_size: int = 3
    camera_index: int = 0
    mirror_frame: bool = True
    draw_landmarks: bool = False
    window_title: str = "Index-Rectangle Inverter (MediaPipe, SRP Refactor)"
