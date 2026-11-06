"""Tarif tanıtım yazıları ve püf noktaları (data/texts.json).

Veritabanı şeması değişmesin diye tarif adına göre ayrı bir dosyada tutulur.
"""

import json
from pathlib import Path

from core.matcher import normalize

_FILE = Path(__file__).resolve().parent.parent / "data" / "texts.json"


def load_texts(path=None):
    """{normalize(tarif adı): {"desc": ..., "tip": ...}}; dosya yoksa boş sözlük."""
    path = Path(path) if path else _FILE
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {normalize(name): value for name, value in raw.items()}


def describe(name, texts):
    """Tarifin tanıtım cümlesi; yoksa boş metin."""
    return (texts.get(normalize(name)) or {}).get("desc", "")


def tip_for(name, texts):
    """Tarifin püf noktası; yoksa boş metin."""
    return (texts.get(normalize(name)) or {}).get("tip", "")
