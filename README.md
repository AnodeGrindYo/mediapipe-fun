# 🖐️ Inversion de couleurs contrôlée par les index (MediaPipe + OpenCV)

Ce projet utilise **MediaPipe** pour détecter les deux index de vos mains via la webcam, et inverse en temps réel les couleurs de la zone délimitée par ces deux doigts.
C’est un petit démonstrateur de **vision par ordinateur interactive**, combinant détection de gestes, traitement d’image et retour visuel instantané.

---

## 🧬 Fonctionnalités

* Suivi des **deux index** à l’aide de MediaPipe Hands
* Création d’un **rectangle dynamique** entre les deux doigts
* **Inversion des couleurs** à l’intérieur de ce rectangle
* **Lissage** des mouvements (EMA) pour éviter les tremblements
* **Affichage FPS**, aide à l’écran et raccourcis clavier

---

## ⚙️ Installation et exécution

### 1️⃣ Créer un environnement virtuel

Sous **Windows** :

```bash
python -m venv .venv
```

Sous **Linux / macOS** :

```bash
python3 -m venv .venv
```

### 2️⃣ Activer l’environnement

Sous **Windows** :

```bash
.venv\Scripts\activate
```

Sous **Linux / macOS** :

```bash
source .venv/bin/activate
```

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## ▶️ Lancer le projet

Une fois l’environnement activé et les dépendances installées :

```bash
python app.py
```

---

## ⌨️ Contrôles

* **Q** : Quitter le programme
* **R** : Réinitialiser le rectangle / le lissage

---

## 🧠 À propos

Ce programme illustre comment :

* capturer un flux vidéo en temps réel avec **OpenCV** ;
* exploiter **MediaPipe** pour extraire les coordonnées des landmarks des mains ;
* manipuler des tableaux NumPy pour appliquer des effets visuels localisés ;
* structurer le code selon le **principe de responsabilité unique (SRP)** pour une architecture claire et maintenable.

---

💡 **Astuce :** Si la webcam ne se lance pas, essayez de changer l’index de caméra dans `Config.camera_index` (par défa
