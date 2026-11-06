"""Ekipman / yurt modu: bir tarifin hangi mutfak aletlerine ihtiyaç duyduğunu bulur.

Önce data/equipment.json içindeki elle hazırlanmış kayıt kullanılır (tarif adına göre).
Kaydı olmayan tarifler (kendi eklediklerin) için yapılış adımlarındaki kelimelerden tahmin yapılır.
"""

import json
from pathlib import Path

from core.matcher import normalize

TOOLS = ["ocak", "fırın", "ızgara", "blender", "tost makinesi"]

# Mutfak profilleri: ad -> evde bulunan aletler (None = elle seçilecek)
PROFILES = {
    "Tam mutfak": list(TOOLS),
    "Yurt: sadece tek ocak": ["ocak"],
    "Ocaksız: blender + tost makinesi": ["blender", "tost makinesi"],
    "Özel seçim": None,
}

_KEYWORDS = {
    "fırın": ["fırın"],
    "ızgara": ["ızgara", "izgara"],
    "blender": ["blender"],
    "tost makinesi": ["tost makinesi"],
    "ocak": [
        "haşla", "kavur", "sotele", "kaynat", "kızart", "pişir", "buğula", "sac ",
        "tava", "demle", "erit", "ısıt", "karamelize",
    ],
}

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "equipment.json"


def load_overrides(path=_DATA_FILE):
    """data/equipment.json -> {normalize(tarif adı): [aletler]}; dosya yoksa boş sözlük."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {normalize(name): list(tools) for name, tools in raw.items()}


def infer_tools(recipe):
    """Yapılış adımlarındaki kelimelerden alet tahmini. 'Pişir' tek başına ocak sayılır;
    fırın geçiyorsa ocak ayrıca eklenmez (örn. 'fırınla')."""
    text = normalize(" ".join(recipe.get("steps") or []))
    found = {tool for tool, words in _KEYWORDS.items() if any(w in text for w in words)}
    # Fırın / ızgara / tost makinesi varsa ocak sadece ocağa özgü bir fiil geçiyorsa gerekir
    if "ocak" in found and found & {"fırın", "ızgara", "tost makinesi"}:
        stove_only = [w for w in _KEYWORDS["ocak"] if w not in ("pişir", "ısıt", "erit")]
        if not any(w in text for w in stove_only):
            found.discard("ocak")
    return [t for t in TOOLS if t in found]


def tools_for(recipe, overrides=None):
    """Tarifin gerektirdiği aletler (sıralı liste). Boş liste = pişirme gerekmez."""
    overrides = overrides if overrides is not None else {}
    key = normalize(recipe["name"])
    if key in overrides:
        return [t for t in TOOLS if t in overrides[key]]
    return infer_tools(recipe)


def can_make(required, available):
    """Gerekli aletlerin hepsi mevcutsa True."""
    return set(required) <= set(available)


def filter_by_equipment(results, available, overrides=None):
    """match_recipes sonuçlarından, eldeki aletlerle yapılabilenleri bırakır."""
    return [r for r in results if can_make(tools_for(r["recipe"], overrides), available)]
