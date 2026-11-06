"""Tarif kategorisi: Kahvaltı / Yemek / Tatlı. Tarif adına göre belirlenir (veritabanı değişmez)."""

from core.matcher import normalize

CATEGORIES = ["Kahvaltı", "Yemek", "Tatlı"]

# Önce açık istisnalar (ad -> kategori), sonra anahtar kelimeler
_EXPLICIT = {
    "tavuk göğsü tatlısı": "Tatlı", "tavuk göğsü muhallebi": "Tatlı",
    "ayran aşı çorbası": "Yemek", "havuçlu kek": "Tatlı", "kuru kaşarlı omlet": "Kahvaltı",
    "bal kabaklı kek": "Tatlı", "pekmezli tahin": "Kahvaltı", "pekmezli yulaf": "Kahvaltı",
    "meyveli yoğurt": "Kahvaltı", "meyve salatası": "Tatlı", "patlamış mısır": "Yemek",
    "peynir tabağı": "Kahvaltı", "simit peynir tabağı": "Kahvaltı", "hummus tabağı": "Yemek",
    "lor peynirli tabak": "Kahvaltı", "labne dip": "Kahvaltı", "çökelek ezmesi": "Kahvaltı",
    "zeytin ezmesi tost": "Kahvaltı", "avokado ezmesi": "Kahvaltı", "bal kaymak kahvaltı tabağı": "Kahvaltı",
    "çikolata soslu muz": "Tatlı", "granola kasesi": "Kahvaltı", "ev yapımı granola": "Kahvaltı",
    "mercimekli kahvaltı köftesi": "Kahvaltı", "sütlü irmik helvası": "Tatlı", "irmik helvası": "Tatlı",
    "ekmek": "Yemek", "simit": "Kahvaltı", "açma": "Kahvaltı", "bazlama": "Yemek",
    "pankek": "Kahvaltı", "yulaflı pankek": "Kahvaltı", "tuzlu kurabiye": "Yemek",
    "fırında tatlı patates": "Yemek", "kestane şekeri": "Tatlı", "haşlama kestane": "Yemek", "tarçınlı pirinç lapası": "Tatlı",
}

_BREAKFAST = (
    "omlet", "menemen", "yumurta", "tost", "krep", "pankek", "granola", "yulaf", "kahvaltı",
    "pişi", "kuymak", "mıhlama", "çılbır", "waffle", "french toast", "poğaça", "gözleme",
    "muffin yumurta", "hamur kızartması", "sigara böreği", "pastırmalı yumurta", "gece yulafı",
    "çökelekli", "yağlama", "katmer",
)
_DESSERT = (
    "kek", "kurabiye", "tatlı", "baklava", "kadayıf", "revani", "şekerpare", "lokma", "tulumba",
    "aşure", "güllaç", "kazandibi", "profiterol", "trileçe", "tiramisu", "cheesecake", "brownie",
    "turta", "helva", "sütlaç", "supangle", "keşkül", "zerde", "dondurma", "puding", "lokum",
    "muhallebi", "komposto", "hoşaf", "pasta", "sufle", "sütlü tatlı", "chia", "yulaf barı",
)


def category_of(name):
    """Tarif adından kategori: 'Kahvaltı', 'Yemek' ya da 'Tatlı'."""
    n = normalize(name)
    if n in _EXPLICIT:
        return _EXPLICIT[n]
    words = n.split()
    if any(w.startswith(k) for w in words for k in _DESSERT) and "çorba" not in n:
        return "Tatlı"
    if any(k in n for k in _BREAKFAST):
        return "Kahvaltı"
    return "Yemek"


def filter_by_category(recipes, category):
    """category: None/'Tümü' ya da CATEGORIES'ten biri; tarif sözlüklerini süzer."""
    if not category or category == "Tümü":
        return list(recipes)
    return [r for r in recipes if category_of(r["name"]) == category]
