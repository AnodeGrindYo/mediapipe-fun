"""
Module : overlay.py
-------------------
Ce module définit la classe `OverlayDrawer`, responsable du dessin de tous les éléments
visuels superposés sur la vidéo : points, rectangle de sélection, messages d’aide (HUD),
et affichage du nombre d’images par seconde (FPS).

Rôle dans l’application
-----------------------
- Fournir une couche visuelle indépendante de la logique métier (séparation des responsabilités).
- Centraliser tous les appels à OpenCV relatifs au rendu graphique.
- Assurer la cohérence visuelle entre les différents éléments (couleurs, polices, styles).

Principe de conception
----------------------
Chaque méthode de cette classe a une responsabilité unique :
- `draw_points` : affichage des positions des doigts.
- `draw_rect` : affichage du rectangle de sélection (ROI).
- `hud` : affichage de l’aide utilisateur (raccourcis clavier, consignes).
- `fps` : affichage du nombre d’images par seconde.
"""

import cv2
from typing import List
from .geometry import Point, Rect


class OverlayDrawer:
    """
    Classe responsable du dessin de tous les overlays (superpositions graphiques)
    dans le flux vidéo OpenCV.

    Attributs
    ---------
    _font : int
        Police utilisée pour les textes OpenCV (`cv2.FONT_HERSHEY_SIMPLEX`).

    Exemple
    -------
        drawer = OverlayDrawer()
        drawer.draw_points(frame, [Point(100, 200), Point(300, 400)])
        drawer.draw_rect(frame, Rect(50, 60, 200, 220))
        drawer.hud(frame, "Montrez vos deux index", "[Q] Quitter [R] Reset")
        drawer.fps(frame, 29.8)
    """

    def __init__(self) -> None:
        """
        Initialise la police à utiliser pour tous les affichages textuels.
        """
        self._font = cv2.FONT_HERSHEY_SIMPLEX

    # ----------------------------------------------------------------------
    def draw_points(self, frame, pts: List[Point]) -> None:
        """
        Dessine les points correspondant aux extrémités d’index détectées.

        Paramètres
        ----------
        frame : np.ndarray
            Image sur laquelle dessiner les points.
        pts : List[Point]
            Liste de points 2D représentant les index détectés.

        Détails graphiques
        ------------------
        - Chaque point est dessiné sous forme de double cercle concentrique :
            - Un grand cercle blanc en contour (diamètre 8 px, épaisseur 2 px).
            - Un petit cercle jaune au centre (diamètre 4 px, plein).
        - Cela permet de garder une bonne visibilité quelle que soit la couleur de fond.
        """
        for p in pts:
            cv2.circle(frame, (p.x, p.y), 8, (255, 255, 255), 2)   # contour blanc
            cv2.circle(frame, (p.x, p.y), 4, (0, 255, 255), -1)   # centre jaune plein

    # ----------------------------------------------------------------------
    def draw_rect(self, frame, rect: Rect) -> None:
        """
        Dessine un rectangle à partir de ses coins opposés, ainsi que ses repères visuels.

        Paramètres
        ----------
        frame : np.ndarray
            Image sur laquelle dessiner.
        rect : Rect
            Rectangle à afficher (coordonnées absolues en pixels).

        Détails graphiques
        ------------------
        - Contour : ligne orange-bleutée (BGR = (0, 200, 255)).
        - Coins : petits cercles pleins pour rendre le rectangle plus visible.
        - Épaisseur : 2 px.
        """
        # Rectangle principal
        cv2.rectangle(frame, (rect.x1, rect.y1), (rect.x2, rect.y2), (0, 200, 255), 2)

        # Petits cercles pour marquer les coins opposés
        cv2.circle(frame, (rect.x1, rect.y1), 6, (0, 200, 255), -1)
        cv2.circle(frame, (rect.x2, rect.y2), 6, (0, 200, 255), -1)

    # ----------------------------------------------------------------------
    def hud(self, frame, msg_top: str, msg_bottom: str) -> None:
        """
        Affiche un HUD (Head-Up Display) avec un message principal en haut
        et un message d’aide en bas de la fenêtre.

        Paramètres
        ----------
        frame : np.ndarray
            Image sur laquelle afficher les messages.
        msg_top : str
            Texte d’instruction affiché en haut (ex : consigne à l’utilisateur).
        msg_bottom : str
            Texte affiché en bas (ex : raccourcis clavier ou légende).

        Détails graphiques
        ------------------
        - Couleur : bleu clair (BGR = (180, 220, 255)).
        - Police : Hershey Simplex (lisible et rapide à tracer).
        - Taille : 0.6 (adaptée à un affichage 720p/1080p).
        - Épaisseur : 2 px, avec antialiasing (`cv2.LINE_AA`).
        """
        h = frame.shape[0]  # hauteur de l'image, pour placer le texte du bas
        cv2.putText(frame, msg_top, (10, 24), self._font, 0.6, (180, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, msg_bottom, (10, h - 12), self._font, 0.6, (180, 220, 255), 2, cv2.LINE_AA)

    # ----------------------------------------------------------------------
    def fps(self, frame, fps: float) -> None:
        """
        Affiche le nombre d’images par seconde (FPS) dans le coin supérieur gauche.

        Paramètres
        ----------
        frame : np.ndarray
            Image sur laquelle dessiner.
        fps : float
            Nombre d’images par seconde estimé.

        Détails graphiques
        ------------------
        - Texte vert clair : BGR = (120, 255, 120)
        - Position par défaut : (10, 48) px
        - Taille et style cohérents avec le reste du HUD
        - Format arrondi à une décimale (ex : "29.8 FPS")
        """
        cv2.putText(frame, f"{fps:.1f} FPS", (10, 48), self._font, 0.6, (120, 255, 120), 2, cv2.LINE_AA)
