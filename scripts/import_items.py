import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "items.db"
XLSX_PATH = BASE_DIR / "data" / "items.xlsx"

df = pd.read_excel(XLSX_PATH)

# normalize column names
df.columns = [c.strip().lower() for c in df.columns]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

inserted = 0

for _, row in df.iterrows():
    name = row.get("item_name")

    if pd.isna(name):
        continue

    voi_raw = str(row.get("voi", "")).strip().lower()
    voi = 1 if voi_raw in ["yes", "true", "1"] else 0

    cur.execute("""
        INSERT OR IGNORE INTO items
        (name, category, subcategories, rarity, voi, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name.strip(),
        str(row.get("category", "")).strip().lower(),
        str(row.get("subcategories", "")).strip().lower(),
        str(row.get("rarity", "")).strip().lower(),
        voi,
        str(row.get("notes", "")).strip()
    ))

    if cur.rowcount > 0:
        inserted += 1

conn.commit()
conn.close()

print(f"Imported {inserted} items successfully")
