from core.units import is_comparable, to_base
def normalize(text):
    """Malzeme adını karşılaştırmaya hazırlar: boşlukları siler, küçük harfe çevirir."""
    text = text.strip()
    # Türkçe harf tuzağı: Python "I".lower() işlemini "i" yapar, oysa Türkçede "ı" olmalı.
    text = text.replace("I", "ı").replace("İ", "i")
    return text.lower()


def _enough(pantry_entry, needed_quantity, needed_unit):
    """Evdeki miktar, tarifin istediği miktarı karşılıyor mu?

    Miktar bilinmiyorsa ya da birimler karşılaştırılamıyorsa True döner:
    emin olamadığımızda malzemeyi 'var' kabul ederiz.
    """
    if needed_quantity is None or pantry_entry is None:
        return True
    have_quantity, have_unit = pantry_entry
    if have_quantity is None:
        return True
    if not is_comparable(have_unit, needed_unit):
        return True
    return to_base(have_quantity, have_unit) >= to_base(needed_quantity, needed_unit)


def match_recipe(my_ingredients, recipe):
    """Tek bir tarifi, evdeki malzemelerle karşılaştırır.

    my_ingredients: malzeme adları listesi ya da
                    {ad: (miktar, birim)} biçiminde sözlük.
    """
    if isinstance(my_ingredients, dict):
        pantry = {normalize(k): v for k, v in my_ingredients.items()}
    else:
        pantry = {normalize(item): None for item in my_ingredients}

    have, missing, insufficient = [], [], []

    for item in recipe["ingredients"]:
        # Malzeme ya düz metin ya da {"name":..., "quantity":..., "unit":...}
        if isinstance(item, dict):
            name = normalize(item["name"])
            quantity, unit = item.get("quantity"), item.get("unit")
        else:
            name = normalize(item)
            quantity, unit = None, None

        if name not in pantry:
            missing.append(name)
        elif _enough(pantry[name], quantity, unit):
            have.append(name)
        else:
            have.append(name)
            insufficient.append(name)

    total = len(recipe["ingredients"])
    ratio = len(have) / total if total else 0

    return {
        "recipe": recipe,
        "have": have,
        "missing": missing,
        "insufficient": insufficient,  # var ama yetersiz
        "ratio": ratio,
    }


def match_recipes(my_ingredients, recipes):
    """Tüm tarifleri eşleştirir ve eşleşme oranı yüksek olandan düşüğe sıralar."""
    results = [match_recipe(my_ingredients, recipe) for recipe in recipes]
    return sorted(results, key=lambda result: result["ratio"], reverse=True)