import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "nids.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            flow_index INTEGER NOT NULL,
            src_ip TEXT DEFAULT '192.168.1.10',
            dst_ip TEXT DEFAULT '10.0.0.1',
            confidence REAL NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()