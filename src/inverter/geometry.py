"""
Module : geometry.py
--------------------
Ce module définit deux structures de base :
- `Point` : une coordonnée 2D (x, y).
- `Rect`  : un rectangle défini par deux coins opposés.

Ces deux classes servent à représenter des entités géométriques
simples manipulées dans tout le projet (détection, rendu, effets).

Les classes utilisent le décorateur `@dataclass` pour :
- générer automatiquement les méthodes `__init__`, `__repr__`, `__eq__`, etc.
- améliorer la lisibilité et réduire le code répétitif.
"""

from __future__ import annotations
from dataclasses import dataclass


# ============================================================================
# Classe Point
# ============================================================================
@dataclass
class Point:
    """
    Représente un point 2D dans un espace d'image (ou plan cartésien discret).

    Attributs
    ---------
    x : int
        Coordonnée horizontale du point (pixel ou unité arbitraire).
    y : int
        Coordonnée verticale du point.

    Exemple
    -------
        p = Point(x=120, y=300)
        print(p)  # → Point(x=120, y=300)
    """
    x: int
    y: int


# ============================================================================
# Classe Rect
# ============================================================================
@dataclass
class Rect:
    """
    Représente un rectangle défini par deux coins opposés : (x1, y1) et (x2, y2).

    Convention
    -----------
    - (x1, y1) correspond au coin supérieur gauche.
    - (x2, y2) correspond au coin inférieur droit.
    - Rien n’impose l’ordre initial : la méthode `ordered()` permet de réordonner
      les coordonnées pour garantir cette convention.

    Attributs
    ---------
    x1, y1 : int
        Coordonnées du premier coin (souvent supérieur gauche).
    x2, y2 : int
        Coordonnées du coin opposé (souvent inférieur droit).

    Exemple
    -------
        r = Rect(300, 200, 100, 400)
        print(r.ordered())
        # → Rect(x1=100, y1=200, x2=300, y2=400)
    """

    x1: int
    y1: int
    x2: int
    y2: int

    # ----------------------------------------------------------------------
    def ordered(self) -> "Rect":
        """
        Retourne un rectangle dont les coordonnées sont réordonnées
        pour garantir l’ordre logique :
            x1 ≤ x2 et y1 ≤ y2

        Cela corrige les rectangles dont les coins auraient été fournis
        dans un ordre inversé (par exemple, si on les définit par glisser-déposer).

        Retour
        ------
        Rect
            Nouveau rectangle avec coordonnées ordonnées.

        Exemple
        --------
            Rect(300, 200, 100, 400).ordered()
            → Rect(100, 200, 300, 400)
        """
        a = sorted([self.x1, self.x2])
        b = sorted([self.y1, self.y2])
        return Rect(a[0], b[0], a[1], b[1])

    # ----------------------------------------------------------------------
    def clamp(self, w: int, h: int) -> "Rect":
        """
        Contraint les coordonnées du rectangle à rester à l’intérieur d’une image.

        Paramètres
        ----------
        w : int
            Largeur maximale (limite horizontale droite).
        h : int
            Hauteur maximale (limite verticale basse).

        Retour
        ------
        Rect
            Nouveau rectangle dont les coordonnées sont bornées
            dans [0, w-1] et [0, h-1], puis réordonnées.

        Exemple
        --------
            r = Rect(-10, 50, 5000, 700)
            r.clamp(640, 480)
            → Rect(x1=0, y1=50, x2=639, y2=479)
        """
        x1 = max(0, min(self.x1, w - 1))
        x2 = max(0, min(self.x2, w - 1))
        y1 = max(0, min(self.y1, h - 1))
        y2 = max(0, min(self.y2, h - 1))
        return Rect(x1, y1, x2, y2).ordered()

    # ----------------------------------------------------------------------
    def valid(self, min_size: int) -> bool:
        """
        Vérifie si le rectangle est géométriquement valide,
        c’est-à-dire d’une taille suffisante pour être significative.

        Paramètres
        ----------
        min_size : int
            Taille minimale autorisée en largeur et en hauteur.

        Retour
        ------
        bool
            True si le rectangle est au moins de cette taille,
            False sinon.

        Exemple
        --------
            Rect(10, 10, 12, 12).valid(3) → False
            Rect(10, 10, 20, 15).valid(3) → True
        """
        return (self.x2 - self.x1) >= min_size and (self.y2 - self.y1) >= min_size
