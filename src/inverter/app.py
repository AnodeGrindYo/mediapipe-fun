"""
InverterApp — Application OpenCV/MediaPipe pour inverser les couleurs d'une zone rectangulaire
définie par les positions des deux index de la main, avec superposition d'overlays et adaptation
automatique à la taille de la fenêtre.

Objectif général
----------------
- Capturer des images depuis une webcam.
- Détecter les extrémités des index via un HandTracker.
- Construire dynamiquement un rectangle (deux coins opposés = deux index).
- Appliquer un effet visuel (inversion des couleurs) sur la région d'intérêt (ROI) délimitée.
- Dessiner des overlays (points, rectangle, HUD, FPS).
- Offrir une fenêtre OpenCV redimensionnable avec letterboxing automatique.
- Gérer proprement les entrées clavier (Q=Quit, R=Reset) et la fermeture par la croix [X].

Composants externes (injectés ou importés)
------------------------------------------
- Config               : configuration applicative (index de caméra, titre de fenêtre, miroir, ...).
- Rect, Point          : primitives géométriques (rectangle et point 2D).
- HandTracker          : détection des points d'intérêt (ici extrémités d'index) sur l'image.
- OverlayDrawer        : dessin des overlays (points, rectangle, HUD, FPS).
- RectangleController  : logique de suivi/construction du rectangle selon les points détectés.
- ROIInverter          : effet d'inversion des couleurs sur une ROI.

Notes d'implémentation
----------------------
- Le code vise la simplicité, la lisibilité et une faible latence.
- Le framerate est lissé par un filtre exponentiel (EMA) pour une lecture plus stable.
- L'adaptation au redimensionnement se fait via un letterboxing conservant le ratio,
  afin d'éviter toute déformation.
- La fermeture par la croix est détectée via WND_PROP_VISIBLE pour une sortie propre.
"""

from __future__ import annotations
from typing import Optional, Tuple, List
import time
import cv2
import numpy as np

from .config import Config
from .geometry import Rect, Point
from .hand_tracking import HandTracker
from .overlay import OverlayDrawer
from .rectangle_controller import RectangleController
from .effects import ROIInverter


class InverterApp:
    """
    Application temps réel d'inversion de couleurs sur une ROI définie par deux index.

    Paramètres
    ----------
    cfg : Config
        Objet de configuration contenant, entre autres, l'index de caméra, le titre de la fenêtre,
        et l'option de miroir vidéo.

    Attributs principaux
    --------------------
    cfg : Config
        Configuration de l'application.
    tracker : HandTracker
        Détecteur des extrémités d'index (ou autres points utiles) dans l'image.
    drawer : OverlayDrawer
        Utilitaire de rendu d'overlays (points, rectangle, HUD, FPS).
    rect_ctrl : RectangleController
        Logique pour construire/mettre à jour le rectangle (ROI) à partir des points détectés.
    cap : cv2.VideoCapture
        Flux vidéo de la webcam.
    _last_time : float
        Timestamp de la dernière mesure FPS.
    _fps : float
        Estimation lissée des FPS (filtre EMA).
    """

    def __init__(self, cfg: Config) -> None:
        # Stocke la configuration et instancie les composants.
        self.cfg = cfg
        self.tracker = HandTracker(cfg)
        self.drawer = OverlayDrawer()
        self.rect_ctrl = RectangleController(cfg)

        # Ouvre la webcam ; lève une exception si indisponible.
        self.cap = cv2.VideoCapture(cfg.camera_index)
        if not self.cap.isOpened():
            self.tracker.close()
            raise RuntimeError(f"Unable to open camera index {cfg.camera_index}")

        # Initialisation du suivi de FPS (EMA).
        self._last_time = time.time()
        self._fps = 0.0

        # Crée une fenêtre redimensionnable (l'utilisateur peut librement ajuster la taille).
        cv2.namedWindow(self.cfg.window_title, cv2.WINDOW_NORMAL)
        # Fixe une taille initiale raisonnable ; l'affichage s'adaptera ensuite automatiquement.
        cv2.resizeWindow(self.cfg.window_title, 960, 540)

    # --- Petits utilitaires focalisés (Single-Responsibility helpers) ---

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Capture une image depuis la webcam et applique un éventuel effet miroir.

        Retour
        ------
        frame : np.ndarray | None
            L'image BGR capturée (mirroir optionnel) ou None si la lecture a échoué.
        """
        ok, frame = self.cap.read()
        if not ok:
            return None
        if self.cfg.mirror_frame:
            frame = cv2.flip(frame, 1)
        return frame

    def detect_tips(self, frame: np.ndarray) -> List[Point]:
        """
        Extrait les points d'intérêt (extrémités d'index) depuis une image.

        Paramètres
        ----------
        frame : np.ndarray
            Image BGR actuelle.

        Retour
        ------
        tips : List[Point]
            Liste (éventuellement vide) des positions détectées.
        """
        return self.tracker.process(frame)

    def compute_rect(self, tips: List[Point], shape: Tuple[int, int, int]) -> Optional[Rect]:
        """
        Met à jour/construit le rectangle ROI à partir des points détectés.

        Paramètres
        ----------
        tips : List[Point]
            Points détectés (doivent idéalement contenir deux index).
        shape : tuple
            Dimensions de l'image (H, W, C) pour bornage/validation.

        Retour
        ------
        rect : Rect | None
            Rectangle ROI valide si disponible, sinon None.
        """
        h, w = shape[0], shape[1]
        return self.rect_ctrl.update(tips, w, h)

    def apply_effects(self, frame: np.ndarray, rect: Optional[Rect]) -> None:
        """
        Applique l'effet d'inversion des couleurs sur la ROI si un rectangle est défini.

        Paramètres
        ----------
        frame : np.ndarray
            Image BGR modifiable in-place.
        rect : Rect | None
            Rectangle ROI cible ; aucun effet si None.
        """
        if rect:
            ROIInverter.invert_inplace(frame, rect)

    def draw_overlays(self, frame: np.ndarray, tips: List[Point], rect: Optional[Rect]) -> None:
        """
        Dessine les overlays sur l'image : points, rectangle, HUD d'aide et FPS.

        Paramètres
        ----------
        frame : np.ndarray
            Image BGR cible du dessin.
        tips : List[Point]
            Points détectés (affichés comme repères).
        rect : Rect | None
            Rectangle ROI (dessiné s'il existe).
        """
        # Affiche les points détectés (ex. extrémités d'index).
        self.drawer.draw_points(frame, tips)

        # Encadre la ROI si elle est définie.
        if rect:
            self.drawer.draw_rect(frame, rect)

        # Affiche un HUD d'aide (consignes + raccourcis).
        self.drawer.hud(
            frame,
            "Montrez vos deux index pour inverser les couleurs dans le rectangle.",
            "[Q] Quitter  [R] Reset",
        )

        # Affiche l'estimation courante des FPS.
        self.drawer.fps(frame, self._fps)

    def update_fps(self) -> None:
        """
        Met à jour l'estimation lissée des FPS via un filtre exponentiel (EMA).

        Détails
        -------
        - Calcule 1/dt où dt est l'intervalle depuis la dernière frame.
        - Met à jour _fps = 0.9 * _fps + 0.1 * (1/dt) pour lisser les fluctuations.
        """
        now = time.time()
        dt = now - self._last_time
        if dt > 0:
            self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt)
        self._last_time = now

    def _current_window_size(self) -> Tuple[int, int]:
        """
        Retourne (width, height) de la fenêtre HighGUI, avec valeur de secours si indisponible.

        Notes
        -----
        - Utilise cv2.getWindowImageRect si disponible (OpenCV ≥ 4.5).
        - Peut renvoyer (960, 540) si la fenêtre est minimisée/indisponible.
        """
        try:
            # OpenCV >= 4.5 : renvoie (x, y, w, h)
            x, y, w, h = cv2.getWindowImageRect(self.cfg.window_title)
            # En cas de fenêtre minimisée, w/h peuvent être 0 → fallback.
            if w <= 0 or h <= 0:
                return (960, 540)
            return (w, h)
        except Exception:
            # Fallback robuste si la fonction n'existe pas/soulève une exception.
            return (960, 540)

    def _fit_to_window(self, frame: np.ndarray) -> np.ndarray:
        """
        Redimensionne l'image pour remplir la fenêtre courante en conservant le ratio (letterboxing).

        Paramètres
        ----------
        frame : np.ndarray
            Image source BGR.

        Retour
        ------
        np.ndarray
            Image redimensionnée/letterboxée pour s'adapter à la fenêtre sans déformation.

        Détails
        -------
        - Calcule un facteur d'échelle commun selon le min des ratios.
        - Centre l'image redimensionnée sur un canvas noir de la taille exacte de la fenêtre.
        """
        target_w, target_h = self._current_window_size()
        if target_w <= 0 or target_h <= 0:
            # Taille indisponible → retourner la frame originale.
            return frame

        # Dimensions source.
        h, w = frame.shape[:2]

        # Échelle isotrope (préserve le ratio).
        scale = min(target_w / w, target_h / h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))

        # Redimensionnement bilinéaire (qualité/rapidité équilibrées).
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Si ça remplit exactement, on renvoie tel quel (pas de letterboxing nécessaire).
        if new_w == target_w and new_h == target_h:
            return resized

        # Letterboxing : on centre sur un canvas noir (marges latérales/haut-bas si besoin).
        canvas = np.zeros((target_h, target_w, 3), dtype=frame.dtype)
        off_x = (target_w - new_w) // 2
        off_y = (target_h - new_h) // 2
        canvas[off_y:off_y+new_h, off_x:off_x+new_w] = resized
        return canvas

    def show(self, frame: np.ndarray) -> None:
        """
        Adapte dynamiquement l'affichage à la taille actuelle de la fenêtre, puis affiche l'image.

        Paramètres
        ----------
        frame : np.ndarray
            Image BGR (modifiée en amont par les effets/overlays).
        """
        # Adapte l'image à la fenêtre (redimensionnement + letterboxing si nécessaire).
        adapted = self._fit_to_window(frame)
        cv2.imshow(self.cfg.window_title, adapted)

    def handle_key_or_close(self) -> bool:
        """
        Gère les entrées clavier et la fermeture par la croix [X] de la fenêtre.

        Retour
        ------
        bool
            True pour continuer la boucle principale, False pour quitter proprement.

        Détails
        -------
        - 'q' : quitter l'application.
        - 'r' : réinitialiser l'état du RectangleController (ex. oubli de la ROI).
        - Si la propriété WND_PROP_VISIBLE < 1, considère que la fenêtre a été fermée.
        """
        # 1) Gestion du clavier (non bloquant, attente 1 ms).
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            return False
        if key == ord("r"):
            self.rect_ctrl.reset()

        # 2) Détection de la fermeture via la croix [X] (visibilité de la fenêtre).
        if cv2.getWindowProperty(self.cfg.window_title, cv2.WND_PROP_VISIBLE) < 1:
            return False
        return True

    # --- Boucle principale ---

    def run(self) -> None:
        """
        Exécute la boucle de traitement temps réel jusqu'à fermeture/erreur de capture.

        Étapes par frame
        ----------------
        1) Lecture de la frame depuis la webcam (miroir éventuel).
        2) Détection des index (points) via HandTracker.
        3) Mise à jour/calcul du rectangle ROI via RectangleController.
        4) Application de l'effet d'inversion des couleurs sur la ROI (si valable).
        5) Mise à jour de l'estimation des FPS.
        6) Rendu des overlays (points, rectangle, HUD, FPS).
        7) Affichage adapté à la taille de la fenêtre (letterboxing).
        8) Gestion des entrées clavier et de la fermeture (Q, R, [X]).
        """
        try:
            while True:
                frame = self.read_frame()
                if frame is None:
                    # Fin de flux ou erreur de capture → on sort proprement.
                    break

                tips = self.detect_tips(frame)
                rect = self.compute_rect(tips, frame.shape)
                self.apply_effects(frame, rect)
                self.update_fps()
                self.draw_overlays(frame, tips, rect)
                self.show(frame)

                if not self.handle_key_or_close():
                    # Demande explicite de sortie ou fermeture de la fenêtre.
                    break
        finally:
            # Garantit la libération des ressources même en cas d'exception.
            self.close()

    # --- Gestion des ressources ---

    def close(self) -> None:
        """
        Libère les ressources système : caméra, tracker, fenêtres OpenCV.
        À appeler lors de la sortie pour éviter les fuites de handles.
        """
        self.cap.release()
        self.tracker.close()
        cv2.destroyAllWindows()
