import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

MODEL_PATH = os.path.join("ml", "model.joblib")
TEST_PATH = os.path.join("data", "UNSW_NB15_testing-set.csv")
OUTPUT_IMG = os.path.join("ml", "confusion_matrix.png")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
features = bundle["features"]

test_df = pd.read_csv(TEST_PATH)
X_test = test_df[features]
y_test = test_df["label"]

y_pred = model.predict(X_test)

# Matrice de confusion graphique
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
            xticklabels=["Normal (0)", "Attaque (1)"], 
            yticklabels=["Normal (0)", "Attaque (1)"])
plt.title("Matrice de Confusion — AI-Powered NIDS")
plt.xlabel("Prédiction Modèle")
plt.ylabel("Vérité Terrain")
plt.tight_layout()
plt.savefig(OUTPUT_IMG, dpi=300)
print(f"[+] Graphique de la matrice de confusion sauvegardé dans : {OUTPUT_IMG}")