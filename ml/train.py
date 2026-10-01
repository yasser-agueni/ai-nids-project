import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# 1. Définition des chemins
DATA_DIR = "data"
TRAIN_PATH = os.path.join(DATA_DIR, "UNSW_NB15_training-set.csv")
TEST_PATH = os.path.join(DATA_DIR, "UNSW_NB15_testing-set.csv")
MODEL_OUTPUT_PATH = os.path.join("ml", "model.joblib")

# 2. Caractéristiques clés sélectionnées (légères, numériques et informatives)
SELECTED_FEATURES = [
    "dur",       # Durée de la connexion
    "spkts",     # Nombre de paquets source -> destination
    "dpkts",     # Nombre de paquets destination -> source
    "sbytes",    # Volume en octets source -> destination
    "dbytes",    # Volume en octets destination -> source
    "rate",      # Débit global de paquets par seconde
    "sttl",      # Time to live source (très utile pour détecter les scans/OS)
    "dttl",      # Time to live destination
    "sload",     # Débit binaire source (bits/s)
    "dload"      # Débit binaire destination (bits/s)
]
TARGET_COLUMN = "label"

def train():
    print("[+] Chargement des ensembles de données...")
    if not os.path.exists(TRAIN_PATH) or not os.path.exists(TEST_PATH):
        raise FileNotFoundError(
            f"Veuillez vérifier la présence de {TRAIN_PATH} et {TEST_PATH}."
        )

    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)

    print(f"[+] Lignes train : {len(train_df)}, Lignes test : {len(test_df)}")

    # Extraction des variables explicatives (X) et de la cible (y)
    X_train = train_df[SELECTED_FEATURES]
    y_train = train_df[TARGET_COLUMN]

    X_test = test_df[SELECTED_FEATURES]
    y_test = test_df[TARGET_COLUMN]

    # 3. Entraînement du modèle Random Forest
    print("[+] Entraînement du modèle Random Forest (100 arbres)...")
    clf = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1  # Utilise tous les cœurs CPU disponibles
    )
    clf.fit(X_train, y_train)

    # 4. Évaluation
    print("[+] Évaluation sur l'ensemble de test...")
    y_pred = clf.predict(X_test)

    print("\n--- Matrice de Confusion ---")
    print(confusion_matrix(y_test, y_pred))

    print("\n--- Rapport de Classification ---")
    print(classification_report(y_test, y_pred, target_names=["Normal (0)", "Attaque (1)"]))

    # 5. Export du modèle et des features nécessaires
    bundle = {
        "model": clf,
        "features": SELECTED_FEATURES
    }
    joblib.dump(bundle, MODEL_OUTPUT_PATH)
    print(f"[+] Modèle et métadonnées sauvegardés dans : {MODEL_OUTPUT_PATH}")

if __name__ == "__main__":
    train()