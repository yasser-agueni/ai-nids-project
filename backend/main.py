import os
import io
import joblib
import pandas as pd
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.database import get_connection, init_db

init_db()

app = FastAPI(title="AI-Powered NIDS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "model.joblib")
bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
REQUIRED_FEATURES = bundle["features"]
MAX_FILE_SIZE = 10 * 1024 * 1024

class StatusUpdate(BaseModel):
    status: str

class UserAuth(BaseModel):
    username: str
    password: str

def evaluate_severity(confidence: float) -> str:
    if confidence >= 90.0:
        return "Critique"
    elif confidence >= 75.0:
        return "Haute"
    return "Moyenne"

# ----------------- AUTHENTIFICATION -----------------
@app.post("/api/auth/signup")
def signup(user: UserAuth):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà pris.")
    conn.close()
    return {"message": "Utilisateur créé avec succès"}

@app.post("/api/auth/login")
def login(user: UserAuth):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (user.username, user.password))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")
    return {"username": row["username"], "token": f"fake-jwt-token-for-{row['username']}"}

# ----------------- GESTION DES ANALYSES & FICHIERS -----------------
@app.get("/api/analyses")
def list_analyses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM analyses ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.delete("/api/analyses/{analysis_id}")
def delete_analysis(analysis_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM alerts WHERE analysis_id = ?", (analysis_id,))
    cur.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "analysis_id": analysis_id}

@app.post("/api/predict-file")
async def predict_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .csv sont autorisés.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Taille supérieure à 10 Mo refusée.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV corrompu: {e}")

    missing = [c for c in REQUIRED_FEATURES if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Colonnes manquantes: {', '.join(missing)}")

    X = df[REQUIRED_FEATURES]
    predictions = model.predict(X)
    probs = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else [1.0] * len(predictions)

    total_flows = int(len(df))
    alert_indices = [i for i, p in enumerate(predictions) if p == 1]
    alert_count = len(alert_indices)
    normal_count = total_flows - alert_count
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO analyses (filename, timestamp, total_flows, normal_flows, alert_flows)
        VALUES (?, ?, ?, ?, ?)
    """, (file.filename, now, total_flows, normal_count, alert_count))
    analysis_id = cur.lastrowid

    alerts_to_insert = []
    for idx in alert_indices:
        conf = round(float(probs[idx]) * 100, 2)
        sev = evaluate_severity(conf)
        # Détection ou simulation déterministe d'adresses IP pour le laboratoire
        src_ip = str(df["srcip"].iloc[idx]) if "srcip" in df.columns else f"192.168.1.{(idx % 120) + 10}"
        dst_ip = str(df["dstip"].iloc[idx]) if "dstip" in df.columns else f"10.0.0.{(idx % 50) + 1}"
        alerts_to_insert.append((analysis_id, int(idx), src_ip, dst_ip, conf, sev, "Nouvelle", now))

    cur.executemany("""
        INSERT INTO alerts (analysis_id, flow_index, src_ip, dst_ip, confidence, severity, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

# ----------------- CONSULTATION & ALERTES -----------------
@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT SUM(total_flows) as tf, SUM(normal_flows) as nf, SUM(alert_flows) as af FROM analyses")
    row = cur.fetchone()
    totals = {
        "total_flows": row["tf"] or 0,
        "normal_flows": row["nf"] or 0,
        "alert_flows": row["af"] or 0
    }

    cur.execute("SELECT severity, COUNT(*) as cnt FROM alerts GROUP BY severity")
    by_severity = {r["severity"]: r["cnt"] for r in cur.fetchall()}

    conn.close()
    return {"totals": totals, "by_severity": by_severity}

@app.get("/api/alerts")
def get_alerts(
    severity: Optional[str] = None, 
    status: Optional[str] = None, 
    ip: Optional[str] = None,
    limit: int = 50
):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []

    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if status:
        query += " AND status = ?"
        params.append(status)
    if ip:
        query += " AND (src_ip LIKE ? OR dst_ip LIKE ?)"
        params.extend([f"%{ip}%", f"%{ip}%"])

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.patch("/api/alerts/{alert_id}/status")
def patch_alert_status(alert_id: int, payload: StatusUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE alerts SET status = ? WHERE id = ?", (payload.status, alert_id))
    conn.commit()
    conn.close()
    return {"status": "updated", "alert_id": alert_id}