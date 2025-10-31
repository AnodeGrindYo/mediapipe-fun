"""
Module : hand_tracking.py
-------------------------
Ce module encapsule l'utilisation de MediaPipe Hands dans une classe `HandTracker`,
afin de détecter la position des index dans une image OpenCV en temps réel.

Objectif principal
------------------
- Initialiser et configurer le module MediaPipe Hands selon les paramètres du projet.
- Extraire les coordonnées des extrémités d’index (INDEX_FINGER_TIP) dans une image.
- (Optionnel) Dessiner les repères de main sur l’image (squelettes articulés).
- Fournir une interface simple, orientée objet, pour les autres composants (InverterApp, etc.).

Avantage de cette encapsulation
-------------------------------
En isolant toute la logique MediaPipe ici, on maintient le **principe de responsabilité unique (SRP)** :
- `HandTracker` : détecte les points d’intérêt des mains.
- `InverterApp` : gère la logique applicative et l’affichage.
- `RectangleController` : calcule la région à inverser.

Cela rend le code modulaire, testable et facile à maintenir.
"""

from __future__ import annotations
from typing import List
import cv2
import numpy as np
import mediapipe as mp

from .geometry import Point
from .config import Config


class HandTracker:
    """
    Détecteur d’index de main basé sur MediaPipe Hands.

    Paramètres
    ----------
    cfg : Config
        Configuration globale de l’application (nombre de mains, confiance, etc.).

    Attributs internes
    ------------------
    _mp_hands : module
        Référence au sous-module MediaPipe `solutions.hands` (abstraction pour raccourcis).
    _hands : mp.solutions.hands.Hands
        Objet MediaPipe configuré pour la détection et le suivi des mains.
    _drawer : module
        Utilitaire de dessin MediaPipe (dessin des landmarks et connexions).

    Exemple
    -------
        tracker = HandTracker(cfg)
        points = tracker.process(frame)
        for p in points:
            cv2.circle(frame, (p.x, p.y), 5, (0, 255, 0), -1)
    """

    def __init__(self, cfg: Config) -> None:
        """
        Initialise le tracker MediaPipe Hands avec les paramètres fournis.

        - `max_num_hands` : nombre maximal de mains à détecter.
        - `model_complexity` : complexité du modèle (0=rapide, 1=équilibré, 2=précis).
        - `detection_confidence` : seuil minimal pour accepter une détection initiale.
        - `tracking_confidence` : seuil minimal pour maintenir le suivi.
        """
        self.cfg = cfg
        self._mp_hands = mp.solutions.hands

        # Création d'une instance du modèle MediaPipe Hands configuré dynamiquement.
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,  # Vidéo temps réel (pas une image fixe)
            max_num_hands=cfg.max_num_hands,
            model_complexity=cfg.model_complexity,
            min_detection_confidence=cfg.detection_confidence,
            min_tracking_confidence=cfg.tracking_confidence,
        )

        # Utilitaire MediaPipe pour dessiner les landmarks (si activé).
        self._drawer = mp.solutions.drawing_utils

    # ----------------------------------------------------------------------
    def process(self, bgr_frame: np.ndarray) -> List[Point]:
        """
        Traite une image BGR (OpenCV) pour détecter les extrémités d'index.

        Paramètres
        ----------
        bgr_frame : np.ndarray
            Image issue de la webcam au format BGR.

        Retour
        ------
        List[Point]
            Liste des coordonnées des extrémités d’index (INDEX_FINGER_TIP)
            détectées dans l’image (0, 1 ou 2 mains selon le contexte).

        Détails du pipeline
        -------------------
        1. Conversion BGR → RGB (MediaPipe attend du RGB).
        2. Passage dans le modèle `_hands.process()`.
        3. Pour chaque main détectée :
            - Récupère le landmark correspondant à l’extrémité de l’index.
            - Convertit ses coordonnées normalisées (0–1) en pixels (x, y).
            - Ajoute ces points à la liste `tips`.
        4. (Optionnel) Si `draw_landmarks=True`, dessine le squelette de la main sur l’image.

        Exemple
        --------
            tips = tracker.process(frame)
            if tips:
                print("Index détecté à :", tips[0].x, tips[0].y)
        """
        # Dimensions de l'image pour convertir les coordonnées relatives → absolues.
        h, w = bgr_frame.shape[:2]

        # Conversion de l'espace de couleur : OpenCV utilise BGR, MediaPipe attend RGB.
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)

        # Passage dans le modèle MediaPipe Hands.
        result = self._hands.process(rgb)

        # Liste des extrémités d'index détectées.
        tips: List[Point] = []

        if result.multi_hand_landmarks:
            # Parcours des mains détectées (limité à max_num_hands).
            for hand_lms in result.multi_hand_landmarks[: self.cfg.max_num_hands]:
                # Récupère le landmark correspondant à l'extrémité de l'index.
                lm = hand_lms.landmark[self._mp_hands.HandLandmark.INDEX_FINGER_TIP]

                # Conversion des coordonnées normalisées [0,1] → pixels [0,w/h].
                tips.append(Point(int(lm.x * w), int(lm.y * h)))

                # Si activé dans la config, dessine les landmarks et connexions.
                if self.cfg.draw_landmarks:
                    self._drawer.draw_landmarks(
                        bgr_frame, hand_lms, self._mp_hands.HAND_CONNECTIONS
                    )

        return tips

    # ----------------------------------------------------------------------
    def close(self) -> None:
        """
        Libère proprement les ressources MediaPipe.

        Doit être appelée à la fin du programme pour éviter les fuites
        de mémoire ou de threads internes dans la librairie MediaPipe.
        """
        self._hands.close()
