"""
Module : rectangle_controller.py
--------------------------------
Ce module définit la classe `RectangleController`, chargée de calculer,
suivre et lisser la position du rectangle de sélection (ROI) défini par
les deux index détectés via le `HandTracker`.

Rôle principal
--------------
- Convertir les positions brutes des doigts en un rectangle stable et cohérent.
- Lisser les coordonnées avec un filtre EMA pour éviter les tremblements.
- Contraindre le rectangle à l’intérieur de l’image (via `clamp()`).
- Rejeter les rectangles trop petits (bruit, faux positifs).

Responsabilités selon le SRP (Single Responsibility Principle)
--------------------------------------------------------------
- `HandTracker` détecte les positions des doigts.
- `RectangleController` gère la construction géométrique et le lissage du rectangle.
- `ROIInverter` applique l’effet visuel sur cette région.
"""

from __future__ import annotations
from typing import Optional, List

from .geometry import Point, Rect
from .smoothing import EMASmoother
from .config import Config


class RectangleController:
    """
    Gère la création, la mise à jour et le lissage du rectangle ROI (Region of Interest).

    Ce rectangle est défini par les positions de deux index (gauche/droite).
    Chaque extrémité est filtrée individuellement par un lisseur EMA pour
    garantir un mouvement fluide à l’écran.

    Attributs
    ---------
    cfg : Config
        Objet de configuration contenant les paramètres de lissage et taille minimale.
    _smooth1 : EMASmoother
        Lisseur EMA appliqué au premier point (index 1).
    _smooth2 : EMASmoother
        Lisseur EMA appliqué au second point (index 2).
    _last_rect : Optional[Rect]
        Dernier rectangle valide connu (permet de conserver l’état entre deux frames).

    Exemple
    -------
        rect_ctrl = RectangleController(cfg)
        rect = rect_ctrl.update(points, frame_w, frame_h)
        if rect:
            print("Rectangle détecté :", rect)
    """

    def __init__(self, cfg: Config) -> None:
        """
        Initialise le contrôleur de rectangle avec deux filtres EMA indépendants.

        Paramètres
        ----------
        cfg : Config
            Configuration de l'application contenant :
            - `smooth_alpha` : facteur de lissage (0.0 → très lent, 1.0 → instantané)
            - `min_rect_size` : taille minimale du rectangle en pixels
        """
        self.cfg = cfg

        # Chaque doigt est lissé indépendamment pour stabiliser le rectangle
        self._smooth1 = EMASmoother(cfg.smooth_alpha)
        self._smooth2 = EMASmoother(cfg.smooth_alpha)

        # Dernier rectangle valide détecté (None tant qu'aucune frame valide)
        self._last_rect: Optional[Rect] = None

    # ----------------------------------------------------------------------
    def reset(self) -> None:
        """
        Réinitialise complètement l’état interne du contrôleur.

        - Vide les lisseurs EMA.
        - Supprime le dernier rectangle connu.

        Utilisé lorsque l’utilisateur appuie sur `[R]` (reset manuel) ou
        lorsqu’on souhaite repartir de zéro sans héritage du passé.
        """
        self._smooth1.reset()
        self._smooth2.reset()
        self._last_rect = None

    # ----------------------------------------------------------------------
    def update(self, tips: List[Point], w: int, h: int) -> Optional[Rect]:
        """
        Met à jour le rectangle ROI en fonction des positions actuelles des index.

        Paramètres
        ----------
        tips : List[Point]
            Liste des points détectés par le HandTracker.
            Doit contenir au moins deux points pour définir une diagonale.
        w : int
            Largeur de l’image (pour contraindre le rectangle à l’intérieur).
        h : int
            Hauteur de l’image.

        Retour
        ------
        Rect | None
            Nouveau rectangle valide s’il existe, sinon le dernier rectangle connu,
            ou None s’il n’y a encore aucun rectangle valide.

        Étapes de calcul
        ----------------
        1. Si au moins deux points sont détectés :
            - Applique un lissage EMA séparé sur chacun.
        2. Construit un rectangle entre les deux points lissés.
        3. Trie les coordonnées avec `ordered()` pour garantir (x1 < x2, y1 < y2).
        4. Contraint les bords à l’intérieur du cadre vidéo (`clamp(w, h)`).
        5. Vérifie que le rectangle atteint une taille minimale (`valid()`).
        6. Met à jour `_last_rect` uniquement si le rectangle est valide.
        7. Retourne le rectangle valide courant ou, à défaut, le dernier connu.

        Exemple
        --------
            rect = ctrl.update(points, 1280, 720)
            if rect:
                # rectangle prêt à être utilisé
        """
        if len(tips) >= 2:
            # Applique le lissage EMA sur les deux points détectés
            p1 = self._smooth1.update(tips[0])
            p2 = self._smooth2.update(tips[1])

            # Crée un rectangle à partir des points lissés
            rect = Rect(p1.x, p1.y, p2.x, p2.y).ordered().clamp(w, h)

            # Valide le rectangle avant de le conserver
            if rect.valid(self.cfg.min_rect_size):
                self._last_rect = rect

        # Retourne le rectangle le plus récent (valide ou None)
        return self._last_rect
