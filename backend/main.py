import io
import os
import joblib
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.database import get_connection

app = FastAPI(
    title="AI-Powered NIDS API",
    description="API de détection d'intrusions réseau avec persistance SQLite",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.path.join("ml", "model.joblib")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Modèle introuvable à {MODEL_PATH}")

saved_bundle = joblib.load(MODEL_PATH)
model = saved_bundle["model"]
REQUIRED_FEATURES = saved_bundle["features"]

class StatusUpdate(BaseModel):
    status: str  # 'Nouvelle', 'Examinée', 'Clôturée'

def evaluate_severity(confidence: float) -> str:
    if confidence >= 90.0:
        return "Critique"
    elif confidence >= 75.0:
        return "Haute"
    return "Moyenne"

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "AI-Powered NIDS Backend avec Base SQLite",
        "required_features": REQUIRED_FEATURES
    }

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo max

@app.post("/api/predict-file")
async def predict_file(file: UploadFile = File(...)):
    # 1. Vérification du nom et de l'extension
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400, 
            detail="Extension non autorisée. Seuls les fichiers .csv sont acceptés."
        )

    # 2. Lecture sécurisée et contrôle de taille (anti-DDoS / saturation mémoire)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Fichier trop volumineux. La taille maximale autorisée est de 10 Mo."
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="Le fichier téléversé est vide."
        )

    # 3. Chargement dans Pandas
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Fichier CSV illisible ou corrompu : {str(e)}"
        )

    # 4. Vérification des colonnes requises
    missing_features = [col for col in REQUIRED_FEATURES if col not in df.columns]
    if missing_features:
        raise HTTPException(
            status_code=400,
            detail=f"Colonnes obligatoires manquantes : {', '.join(missing_features)}"
        )

    # 5. Inférence Machine Learning
    try:
        X = df[REQUIRED_FEATURES]
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else [1.0] * len(predictions)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur durant l'évaluation par l'algorithme : {str(e)}"
        )

    total_flows = int(len(df))
    alert_indices = [i for i, p in enumerate(predictions) if p == 1]
    alert_count = len(alert_indices)
    normal_count = total_flows - alert_count
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 6. Enregistrement en base de données
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analyses (filename, timestamp, total_flows, normal_flows, alert_flows)
        VALUES (?, ?, ?, ?, ?)
    """, (file.filename, now, total_flows, normal_count, alert_count))
    analysis_id = cursor.lastrowid

    alerts_to_insert = []
    for idx in alert_indices:
        conf = round(float(probabilities[idx]) * 100, 2)
        sev = evaluate_severity(conf)
        alerts_to_insert.append((analysis_id, int(idx), conf, sev, "Nouvelle", now))

    cursor.executemany("""
        INSERT INTO alerts (analysis_id, flow_index, confidence, severity, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, alerts_to_insert)

    conn.commit()
    conn.close()

    return {
        "analysis_id": analysis_id,
        "filename": file.filename,
        "total_flows": total_flows,
        "normal_flows": normal_count,
        "alert_flows": alert_count,
        "threat_percentage": round((alert_count / total_flows) * 100, 2) if total_flows > 0 else 0.0
    }

@app.get("/api/alerts")
def get_alerts(severity: str = None, status: str = None, limit: int = 50):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@app.patch("/api/alerts/{alert_id}/status")
def update_alert_status(alert_id: int, payload: StatusUpdate):
    valid_statuses = ["Nouvelle", "Examinée", "Clôturée"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Choisissez parmi {valid_statuses}")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET status = ? WHERE id = ?", (payload.status, alert_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Alerte non trouvée.")

    return {"message": "Statut mis à jour avec succès", "alert_id": alert_id, "new_status": payload.status}

@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COALESCE(SUM(total_flows), 0) AS total_flows,
            COALESCE(SUM(normal_flows), 0) AS normal_flows,
            COALESCE(SUM(alert_flows), 0) AS alert_flows
        FROM analyses
    """)
    totals = dict(cursor.fetchone())

    cursor.execute("""
        SELECT severity, COUNT(*) as count 
        FROM alerts 
        GROUP BY severity
    """)
    severities = {row["severity"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM alerts 
        GROUP BY status
    """)
    statuses = {row["status"]: row["count"] for row in cursor.fetchall()}

    conn.close()
    return {
        "totals": totals,
        "by_severity": severities,
        "by_status": statuses
    }