"""
Module : smoothing.py
---------------------
Ce module définit la classe `EMASmoother`, un filtre de lissage temporel basé sur la
moyenne mobile exponentielle (EMA, *Exponential Moving Average*), appliqué ici
aux coordonnées de points détectés (ex. : extrémités d’index).

Objectif
--------
- Lisser les variations rapides entre deux positions successives d’un point.
- Réduire les tremblements et la jitter causés par le bruit de détection.
- Fournir une position "visuellement stable" à l’écran pour une meilleure expérience.

Principe du lissage EMA
-----------------------
À chaque nouvelle position `(nx, ny)` détectée, on calcule une moyenne pondérée
avec la précédente position `(px, py)` selon le facteur de lissage `alpha` :

    lissée = α * nouvelle + (1 - α) * ancienne

- `α` proche de 1 → réponse rapide, mais peu lissée.
- `α` proche de 0 → réponse lente, mais très fluide.

Formule appliquée ici (pour chaque coordonnée) :
    sₓ = px * (1 - α) + nx * α
    sy = py * (1 - α) + ny * α

Résultat : position intermédiaire entre l’ancienne et la nouvelle.
"""

from __future__ import annotations
from typing import Optional
from .geometry import Point


class EMASmoother:
    """
    Implémente un filtre EMA (Exponential Moving Average) pour lisser la trajectoire d’un point.

    Attributs
    ---------
    alpha : float
        Facteur de lissage ∈ [0, 1].
        - 0 → aucun changement (inertie totale).
        - 1 → aucun lissage (réponse instantanée).
    _prev : Optional[Point]
        Dernier point lissé (stocké en mémoire pour la mise à jour suivante).

    Exemple
    -------
        smoother = EMASmoother(alpha=0.4)
        p1 = smoother.update(Point(100, 100))
        p2 = smoother.update(Point(140, 120))
        print(p2)  # Point(x≈116, y≈108)
    """

    def __init__(self, alpha: float) -> None:
        """
        Initialise le filtre EMA avec un facteur de lissage donné.

        Paramètres
        ----------
        alpha : float
            Poids du nouveau point (entre 0 et 1).

        Exceptions
        ----------
        ValueError :
            Si alpha est en dehors de [0,1].
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError("alpha must be in [0,1]")

        # Poids de la nouvelle valeur par rapport à l’ancienne
        self.alpha = alpha

        # Dernier point mémorisé (None tant que non initialisé)
        self._prev: Optional[Point] = None

    # ----------------------------------------------------------------------
    def update(self, new_p: Point) -> Point:
        """
        Met à jour la position lissée à partir d’un nouveau point détecté.

        Paramètres
        ----------
        new_p : Point
            Nouvelle position brute à lisser.

        Retour
        ------
        Point
            Point lissé selon la formule EMA.

        Détails du comportement
        -----------------------
        - Si aucun point précédent (_prev) n’existe encore, la sortie = entrée.
        - Sinon, calcule une moyenne pondérée des coordonnées :
              sx = px * (1 - α) + nx * α
              sy = py * (1 - α) + ny * α
        - Le résultat est converti en entiers pour correspondre à des coordonnées pixel.

        Exemple
        --------
            smooth = EMASmoother(0.4)
            p = smooth.update(Point(120, 130))
            q = smooth.update(Point(140, 150))
            → q ≈ Point(128, 138)
        """
        # Cas d’initialisation : premier point observé
        if self._prev is None:
            self._prev = new_p
            return new_p

        # Coordonnées précédentes (px, py)
        px, py = self._prev.x, self._prev.y
        # Coordonnées nouvelles (nx, ny)
        nx, ny = new_p.x, new_p.y

        # Lissage EMA (moyenne pondérée)
        sx = int(px * (1 - self.alpha) + nx * self.alpha)
        sy = int(py * (1 - self.alpha) + ny * self.alpha)

        # Mémorise et renvoie le nouveau point lissé
        self._prev = Point(sx, sy)
        return self._prev

    # ----------------------------------------------------------------------
    def reset(self) -> None:
        """
        Réinitialise le filtre, effaçant la mémoire du dernier point.

        Utile pour recommencer le lissage à zéro (ex. : après un reset utilisateur).
        """
        self._prev = None
