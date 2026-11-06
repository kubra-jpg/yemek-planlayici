"""data/recipes.json içindeki tarifleri mevcut veritabanına uygular.

- Veritabanında olmayan tarifleri ekler.
- Aynı adlı tariflerin süre, malzeme ve adımlarını günceller (favoriler korunur).
- data/removed.json'daki (kaldırılan) tarifleri siler; kendi eklediğin tariflere dokunmaz.
- Dolabına, alışveriş listene ve kendi eklediğin (adı JSON'da olmayan) tariflere dokunmaz.

Kullanım (uygulama kapalıyken):  python update_recipes.py
"""

import json
from pathlib import Path

from core import repository as repo
from core.db import get_session, init_db

init_db()
data = json.loads((Path(__file__).parent / "data" / "recipes.json").read_text(encoding="utf-8"))

with get_session() as session:
    before = {r["name"]: r for r in repo.list_recipes(session)}

added = updated = skipped = 0
problems = []
with get_session() as session:
    for r in data:
        payload = {
            "name": r["name"],
            "time_min": r["time_min"],
            "servings": r["servings"],
            "ingredients": r["ingredients"],
            "steps": "\n".join(r["steps"]),
        }
        old = before.get(r["name"])
        try:
            if old is None:
                repo.save_recipe(session, payload, None)
                added += 1
            elif old["steps"] != r["steps"] or old["time_min"] != r["time_min"]:
                repo.save_recipe(session, payload, old["id"])
                updated += 1
            else:
                skipped += 1
        except ValueError as error:
            problems.append((r["name"], str(error)))

# Kaldırılan tarifleri (içecekler) sil
removed_file = Path(__file__).parent / "data" / "removed.json"
deleted = 0
if removed_file.exists():
    removed_names = set(json.loads(removed_file.read_text(encoding="utf-8")))
    with get_session() as session:
        for r in repo.list_recipes(session):
            if r["name"] in removed_names:
                repo.delete_recipe(session, r["id"])
                deleted += 1

# Favori durumu değiştiyse eski haline getir
with get_session() as session:
    after = {r["name"]: r for r in repo.list_recipes(session)}
    restored = 0
    for name, old in before.items():
        new = after.get(name)
        if new is not None and bool(new["is_favorite"]) != bool(old["is_favorite"]):
            repo.toggle_favorite(session, new["id"])
            restored += 1

print(f"{added} yeni tarif eklendi, {updated} tarif güncellendi, {skipped} tarif zaten güncel.")
if deleted:
    print(f"{deleted} tarif (içecekler) silindi.")
if restored:
    print(f"{restored} tarifin favori durumu korundu.")
for name, message in problems:
    print("Sorun:", name, "-", message)
