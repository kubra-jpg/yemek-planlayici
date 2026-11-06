"""Pişirme geçmişi ve puanlar: tarif adına göre tutulur (tarif numarası değişse de kaybolmaz)."""

import json
from datetime import date
from pathlib import Path


def load_history(path):
    """Geçmiş dosyasını okur; yoksa ya da bozuksa boş liste döndürür."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        entries = []
        for e in data:
            rating = e.get("rating")
            if rating is not None:
                rating = min(max(int(rating), 1), 5)
            entries.append({"name": str(e["name"]), "date": str(e["date"]), "rating": rating})
        return entries
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return []


def save_history(path, history):
    Path(path).write_text(json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")


def add_entry(history, name, rating=None, today=None):
    """Yeni kayıt ekler, eklenen kaydın sırasını (indeksini) döndürür."""
    history.append({"name": name, "date": (today or date.today()).isoformat(), "rating": rating})
    return len(history) - 1


def set_rating(history, index, rating):
    if 0 <= index < len(history):
        history[index]["rating"] = rating


def stats(history, name):
    """Bir tarifin özeti: kaç kez yapıldı, son tarih, ortalama puan."""
    rows = [e for e in history if e["name"] == name]
    if not rows:
        return {"count": 0, "last": None, "avg": None}
    rated = [e["rating"] for e in rows if e["rating"]]
    return {
        "count": len(rows),
        "last": max(e["date"] for e in rows),
        "avg": round(sum(rated) / len(rated), 1) if rated else None,
    }


def format_date(iso):
    """2026-11-05 -> 05.11.2026"""
    try:
        y, m, d = iso.split("-")
        return f"{int(d):02d}.{int(m):02d}.{y}"
    except ValueError:
        return iso


def sort_by_history(results, history, by):
    """Sonuçları geçmişe göre sıralar.

    by="rating": puanı yüksek olan önce (puansızlar en sonda).
    by="last": hiç yapılmayanlar ve en uzun süredir yapılmayanlar önce.
    """
    cache = {}

    def info(r):
        name = r["recipe"]["name"]
        if name not in cache:
            cache[name] = stats(history, name)
        return cache[name]

    if by == "rating":
        return sorted(results, key=lambda r: -(info(r)["avg"] or 0))
    if by == "last":
        return sorted(results, key=lambda r: info(r)["last"] or "")
    return list(results)


def recent(history, limit=15):
    """En yeni kayıtlar önce olacak şekilde, (sıra numarası, kayıt) çiftleri."""
    return list(reversed(list(enumerate(history))))[:limit]


def top_rated(history, limit=5):
    """Ortalama puanı en yüksek tarifler: [(ad, ortalama, kez)]; en az bir puan şart."""
    names = {e["name"] for e in history if e["rating"]}
    rows = []
    for n in names:
        s = stats(history, n)
        rows.append((n, s["avg"], s["count"]))
    rows.sort(key=lambda x: (-x[1], -x[2], x[0]))
    return rows[:limit]
