import os
import sqlite3
from backend.database import init_db, DB_PATH

# 1. Supprime l'ancienne base verrouillée ou obsolète
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
        print("[+] Ancienne base supprimée.")
    except Exception as e:
        print(f"[!] Erreur suppression fichier : {e}")

# 2. Recrée les tables avec src_ip, dst_ip et users
init_db()

# 3. Insère le compte administrateur par défaut
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
conn.commit()
conn.close()

print("[+] Nouvelle base SQLite initialisée avec succès !")
print("[+] Identifiants : admin / admin123")