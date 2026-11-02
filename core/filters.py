"""Tarif arama, filtreleme ve sıralama (arayüzden bağımsız)."""
from core.matcher import normalize

# Türkçe alfabe sırası: Python varsayılan olarak ç, ğ, ı, ö, ş, ü harflerini z'den sonraya koyar
_TR_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyz"


def turkish_key(text):
    """Metni Türkçe alfabeye göre sıralanabilir bir anahtara çevirir."""
    return [
        _TR_ALPHABET.index(ch) if ch in _TR_ALPHABET else 100 + ord(ch)
        for ch in normalize(text)
    ]


def _ingredient_name(item):
    return item["name"] if isinstance(item, dict) else item


def filter_recipes(recipes, query="", max_time=None, favorites_only=False):
    """Tarifleri arama metni, süre ve favori durumuna göre süzer.

    Arama metni tarif adında ya da malzemelerinden birinde geçiyorsa tarif eşleşir.
    """
    q = normalize(query) if query else ""
    result = []
    for recipe in recipes:
        if favorites_only and not recipe.get("is_favorite"):
            continue
        if max_time is not None and recipe.get("time_min", 0) > max_time:
            continue
        if q:
            texts = [normalize(recipe["name"])] + [
                normalize(_ingredient_name(i)) for i in recipe["ingredients"]
            ]
            if not any(q in text for text in texts):
                continue
        result.append(recipe)
    return result


SORT_LABELS = {
    "match": "Eşleşme oranı",
    "time": "Hazırlama süresi",
    "name": "Tarif adı",
}


def sort_results(results, by="match"):
    """match_recipes sonuçlarını sıralar."""
    if by == "time":
        return sorted(results, key=lambda r: r["recipe"]["time_min"])
    if by == "name":
        return sorted(results, key=lambda r: turkish_key(r["recipe"]["name"]))
    # Varsayılan: eşleşme oranı yüksek olan önce, eşitse kısa süren önce
    return sorted(results, key=lambda r: (-r["ratio"], r["recipe"]["time_min"]))