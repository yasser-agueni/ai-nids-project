# AI-Powered Network Intrusion Detection System (NIDS)

Système de détection d'intrusions réseau combinant l'apprentissage automatique (Random Forest), une API REST sécurisée (FastAPI), une base de données d'audit (SQLite) et un tableau de bord analytique réactif (React + Vite).

---

## Architecture du Projet

* **`ml/`** : Scripts d'entraînement et d'évaluation du modèle sur le jeu de données UNSW-NB15.
* **`backend/`** : API FastAPI assurant la validation des flux, l'inférence ML et la persistance SQLite (`nids.db`).
* **`frontend/`** : Interface SOC (Security Operations Center) développée avec React, Vite et Recharts.
* **`data/`** : Fichiers d'échantillons et jeux de démonstration (`demo_normal.csv`, `demo_attack.csv`).

---

## Guide d'Installation et d'Exécution

### 1. Prérequis
* Python 3.10+
* Node.js 18+

### 2. Démarrage du Backend
```bash
# Activation de l'environnement virtuel
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac

# Lancement du serveur FastAPI
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000