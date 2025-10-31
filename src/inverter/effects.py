"""
Module : effects.py
-------------------
Contient la classe `ROIInverter`, responsable de l’application d’un effet visuel
(inversion des couleurs) sur une région rectangulaire d’une image OpenCV (ROI).

Principe de l’effet :
---------------------
- On sélectionne une sous-zone (Region of Interest) définie par un rectangle (`Rect`).
- On inverse les couleurs en soustrayant les valeurs RGB à 255 (effet "négatif").
- L’opération se fait **in-place** : l’image d’origine est directement modifiée,
  sans création de nouvelle copie (gain de performance et de mémoire).

Utilisation typique :
---------------------
    rect = Rect(x1=100, y1=200, x2=300, y2=400)
    ROIInverter.invert_inplace(frame, rect)

    # Résultat : la zone (100→300, 200→400) de l'image 'frame' est inversée.
"""

import numpy as np
from .geometry import Rect


class ROIInverter:
    """
    Classe utilitaire fournissant des effets d'image basés sur des régions rectangulaires (ROI).

    Pour le moment, elle ne contient qu'un seul effet : l'inversion des couleurs.
    Cette approche (classe statique) permet d'ajouter facilement d'autres effets ultérieurement,
    tout en gardant un regroupement logique et cohérent (principe de responsabilité unique — SRP).
    """

    @staticmethod
    def invert_inplace(frame: np.ndarray, rect: Rect) -> None:
        """
        Inverse les couleurs de la région d'intérêt (ROI) définie par le rectangle `rect`.

        L'opération se fait **en place**, c’est-à-dire que le tableau `frame` est directement modifié.

        Paramètres
        ----------
        frame : np.ndarray
            Image couleur en format BGR (issue d’OpenCV).
        rect : Rect
            Rectangle définissant la région d'intérêt, avec coordonnées (x1, y1) pour le coin
            supérieur gauche et (x2, y2) pour le coin inférieur droit.

        Effet
        -----
        Chaque pixel de la zone sélectionnée est remplacé par (255 - valeur),
        produisant un effet de **négatif photographique**.

        Exemple
        --------
        Si un pixel avait la valeur [0, 128, 255], il devient [255, 127, 0].
        """
        # Sélectionne la région d'intérêt (ROI) dans l'image.
        roi = frame[rect.y1:rect.y2, rect.x1:rect.x2]

        # Inversion des valeurs RGB : 255 - valeur actuelle
        # ⚠️ Opération in-place : le résultat est directement réécrit dans 'frame'
        frame[rect.y1:rect.y2, rect.x1:rect.x2] = 255 - roi
