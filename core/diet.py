"""Diyet ve alerji filtreleri: malzeme adından alerjen etiketi çıkarır, tarifleri süzer.

Etiketleme malzeme adındaki anahtar sözcüklere dayanır (kullanıcının eklediği
malzemelerde de çalışsın diye). Emin olunamayan işlenmiş ürünlerde (çikolata,
bisküvi, soya sosu...) temkinli davranılır: şüpheli alerjen var sayılır.
"""

import json
from functools import lru_cache
from pathlib import Path

from core.matcher import normalize

# etiket -> (tam eşleşen kısa sözcükler, önek olarak eşleşen sözcükler)
_RULES = {
    "et": (
        {"et"},
        ("kıyma", "tavuk", "kuzu", "dana", "sucuk", "pastırma", "ciğer", "işkembe",
         "paça", "sosis", "salam", "hindi", "köfte", "kemik"),
    ),
    "deniz": (
        set(),
        ("balık", "balığ", "karides", "midye", "kalamar", "levrek", "çupra", "somon", "hamsi",
         "sardalya", "uskumru", "palamut", "alabalık", "ahtapot", "istakoz", "yengeç"),
    ),
    "süt": (
        set(),
        ("süt", "yoğurt", "peynir", "kaşar", "tereyağ", "krema", "labne", "mascarpone",
         "kaymak", "parmesan", "mozzarella", "dondurma", "ayran", "çikolata", "bisküvi"),
    ),
    "yumurta": (set(), ("yumurta", "mayonez", "kedi")),
    "gluten": (
        {"un"},
        ("makarna", "spagetti", "ekmek", "bulgur", "buğday", "irmik", "yufka", "lavaş",
         "erişte", "şehriye", "noodle", "galeta", "bisküvi", "kadayıf", "tarhana",
         "simit", "lazanya", "yulaf", "arpa", "tutmaç", "pide", "kedi", "güllaç", "soya sos"),
    ),
    "kuruyemiş": (set(), ("ceviz", "badem", "fındık", "fıstı", "kaju")),
    "susam": (set(), ("susam", "tahin", "simit")),
    "soya": (set(), ("soya",)),
    "bal": ({"bal"}, ()),
}

# Bunlar bir sözcük eşleşse bile etiket taşımaz
_EXCEPTIONS = [
    ({"mısır", "un"}, "gluten"),  # mısır unu glütensizdir
]

LABELS = {
    "et": "et",
    "deniz": "balık/deniz ürünü",
    "süt": "süt ürünü",
    "yumurta": "yumurta",
    "gluten": "gluten",
    "kuruyemiş": "kuruyemiş",
    "susam": "susam",
    "soya": "soya",
    "bal": "bal",
}

# Kullanıcıya gösterilen diyetler -> yasak etiketler
DIETS = {
    "Fark etmez": set(),
    "Vejetaryen": {"et", "deniz"},
    "Pesketaryen": {"et"},
    "Vegan": {"et", "deniz", "süt", "yumurta", "bal"},
    "Glütensiz": {"gluten"},
}

# Kullanıcıya gösterilen alerjiler -> yasak etiketler
ALLERGIES = {
    "Süt": {"süt"},
    "Yumurta": {"yumurta"},
    "Gluten": {"gluten"},
    "Kuruyemiş (ceviz, fıstık, badem...)": {"kuruyemiş"},
    "Susam / tahin": {"susam"},
    "Soya": {"soya"},
    "Balık ve deniz ürünleri": {"deniz"},
}


@lru_cache(maxsize=4096)
def ingredient_tags(name):
    """Bir malzeme adının taşıdığı etiketler kümesi (aynı ad için bir kez hesaplanır)."""
    text = normalize(name)
    words = set(text.split())
    tags = set()
    for tag, (exact, prefixes) in _RULES.items():
        hit = bool(words & exact) or any(
            w.startswith(p) or p in text for p in prefixes for w in words
        )
        if hit:
            tags.add(tag)
    for needed, tag in _EXCEPTIONS:
        if needed <= words:
            tags.discard(tag)
    return frozenset(tags)


def recipe_tags(recipe):
    tags = set()
    for ing in recipe["ingredients"]:
        tags |= ingredient_tags(ing["name"])
    return tags


def forbidden_tags(diet="Fark etmez", allergies=()):
    banned = set(DIETS.get(diet, set()))
    for a in allergies:
        banned |= ALLERGIES.get(a, set())
    return banned


def filter_by_diet(recipes, diet="Fark etmez", allergies=()):
    """Seçilen diyet ve alerjilere uymayan tarifleri eler."""
    banned = forbidden_tags(diet, allergies)
    if not banned:
        return list(recipes)
    return [r for r in recipes if not (recipe_tags(r) & banned)]


def contains_text(recipe):
    """Kartta gösterilecek 'İçerir: ...' metni (etiket yoksa boş)."""
    shown = [LABELS[t] for t in LABELS if t in recipe_tags(recipe)]
    return ", ".join(shown)


def load_settings(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        diet = data.get("diet", "Fark etmez")
        if diet not in DIETS:
            diet = "Fark etmez"
        allergies = [a for a in data.get("allergies", []) if a in ALLERGIES]
        return {"diet": diet, "allergies": allergies}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"diet": "Fark etmez", "allergies": []}


def save_settings(path, settings):
    Path(path).write_text(json.dumps(settings, ensure_ascii=False, indent=1), encoding="utf-8")
