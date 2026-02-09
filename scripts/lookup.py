import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "items.db"

def search_items(query):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, category, subcategories, rarity, voi
        FROM items
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 15
    """, (f"%{query}%",))

    results = cur.fetchall()
    conn.close()
    return results


if __name__ == "__main__":
    while True:
        q = input("\nSearch item (or 'exit'): ").strip()
        if q.lower() == "exit":
            break

        results = search_items(q)

        if not results:
            print("No items found.")
            continue

        for name, cat, sub, rarity, voi in results:
            voi_tag = " | VOI" if voi else ""
            print(f"- {name} [{sub} | {rarity}]{voi_tag}")
