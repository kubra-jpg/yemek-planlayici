"""data/recipes.json içindeki yeni tarifleri veritabanına ekler.

Evdeki malzemeler, alışveriş listesi ve arayüzden eklenen tarifler korunur.
"""
from pathlib import Path

from core import repository as repo
from core.db import get_session, init_db

init_db()
with get_session() as session:
    added = repo.import_recipes(session, Path(__file__).parent / "data" / "recipes.json")
print(f"{added} yeni tarif eklendi.")