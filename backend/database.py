import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "nids.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table 1: Historique des analyses de fichiers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            total_flows INTEGER NOT NULL,
            normal_flows INTEGER NOT NULL,
            alert_flows INTEGER NOT NULL
        )
    """)

    # Table 2: Alertes de sécurité individuelles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            flow_index INTEGER NOT NULL,
            confidence REAL NOT NULL,
            severity TEXT NOT NULL,
            status TEXT DEFAULT 'Nouvelle',
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analyses (id)
        )
    """)
    conn.commit()
    conn.close()

# Initialisation immédiate des tables
init_db()