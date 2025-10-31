"""
main.py
--------
Point d’entrée principal du programme "Index-Rectangle Inverter".

Ce fichier :
- Configure l’environnement Python pour pouvoir importer les modules internes.
- Crée la configuration de l’application (`Config`).
- Instancie et exécute l’application principale (`InverterApp`).

Objectif du projet :
--------------------
Ce projet permet d’inverser les couleurs d’une zone rectangulaire de la webcam,
définie par les positions de vos deux index, détectés grâce à MediaPipe.
Le tout s’affiche en temps réel avec OpenCV.

Organisation du code :
----------------------
📁 src/inverter/
   ├── app.py                 → logique principale de l’application
   ├── config.py              → configuration et paramètres
   ├── geometry.py            → définitions géométriques (points, rectangles)
   ├── smoothing.py           → lisseur EMA (stabilisation)
   ├── hand_tracking.py       → détection des index via MediaPipe
   ├── rectangle_controller.py → gestion et lissage du rectangle ROI
   ├── overlay.py             → affichage graphique (points, HUD, FPS)
   └── effects.py             → effets visuels (inversion de couleurs)
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1️⃣  Ajustement du chemin d'import
# ---------------------------------------------------------------------------
# Quand on exécute ce script directement, Python ne connaît pas forcément le
# dossier "src" comme module. On doit donc l'ajouter manuellement au chemin
# de recherche des modules (sys.path).
#
# Exemple :
#   sys.path contient les dossiers où Python cherche les imports.
#   Ici, on ajoute le dossier "src" pour pouvoir faire :
#       from inverter.app import InverterApp
#   sans erreur "ModuleNotFoundError".
#
# ⚠️ Cette ligne ne modifie rien au code métier, elle sert seulement à
# permettre les imports locaux lorsque le projet est lancé depuis la racine.
# ---------------------------------------------------------------------------
sys.path.append(str(Path(__file__).resolve().parent / "src"))

# ---------------------------------------------------------------------------
# 2️⃣  Import des composants principaux
# ---------------------------------------------------------------------------
# On importe les deux briques centrales :
# - Config      : contient tous les paramètres de l’application.
# - InverterApp : classe principale qui orchestre tout le fonctionnement
#                 (caméra, détection, affichage, effets…).
# ---------------------------------------------------------------------------
from inverter.app import InverterApp
from inverter.config import Config


# ---------------------------------------------------------------------------
# 3️⃣  Fonction main()
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Point d’entrée principal de l’application.

    Étapes :
    --------
    1. Création de la configuration (`Config`).
       - Définit les paramètres de la caméra, du suivi, de l’affichage…
       - Peut être modifiée par l’utilisateur avant le lancement.

    2. Instanciation de l’application (`InverterApp`).
       - Prépare la capture vidéo.
       - Initialise MediaPipe pour la détection des mains.
       - Crée la fenêtre OpenCV.

    3. Lancement de la boucle principale (`app.run()`).
       - Lit les images de la webcam.
       - Détecte les index.
       - Calcule le rectangle ROI.
       - Applique l’effet d’inversion de couleurs.
       - Dessine les overlays (points, rectangle, HUD, FPS).
       - Met à jour la fenêtre jusqu’à ce que l’utilisateur quitte (Q ou X).

    En résumé :
    -----------
        Config  →  InverterApp  →  .run()

    Sortie :
    --------
    - L’application ouvre une fenêtre interactive.
    - Affiche le flux de la webcam avec un rectangle qui inverse les couleurs
      entre vos deux index.

    Raccourcis clavier :
    --------------------
    [Q] → Quitter l’application proprement.
    [R] → Réinitialiser le rectangle et les filtres de lissage.
    """
    # Étape 1 : création de la configuration
    cfg = Config()

    # Étape 2 : création de l’application principale
    app = InverterApp(cfg)

    # Étape 3 : lancement de la boucle principale
    app.run()


# ---------------------------------------------------------------------------
# 4️⃣  Point d’entrée conditionnel
# ---------------------------------------------------------------------------
# Cette condition spéciale `if __name__ == "__main__":` indique à Python :
# - "Exécute la fonction main() uniquement si ce fichier est lancé directement."
# - Si ce fichier est importé comme module dans un autre script, `main()` NE
#   sera pas appelé automatiquement.
#
# C’est une bonne pratique universelle en Python pour séparer :
# - le **code exécutable** (main)
# - du **code importable** (modules)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
