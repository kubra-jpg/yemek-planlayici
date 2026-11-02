from core.units import is_comparable, to_base


def normalize(text):
    """Malzeme adını karşılaştırmaya hazırlar: boşlukları siler, küçük harfe çevirir."""
    text = text.strip()
    # Türkçe harf tuzağı: Python "I".lower() işlemini "i" yapar, oysa Türkçede "ı" olmalı.
    text = text.replace("I", "ı").replace("İ", "i")
    return text.lower()


def _words(name):
    return set(name.split())


def find_in_pantry(name, pantry):
    """Tarifteki malzemeyi evdeki malzemeler arasında arar.

    Önce birebir eşleşme, bulunamazsa kelime bazlı eşleşme denenir:
    'mercimek' ile 'kırmızı mercimek' eşleşir (biri diğerinin tüm kelimelerini içerir).
    Bulunan evdeki malzemenin adını, bulunamazsa None döndürür.
    """
    if name in pantry:
        return name
    needed = _words(name)
    for key in pantry:
        have = _words(key)
        if have <= needed or needed <= have:
            return key
    return None


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


def match_recipe(my_ingredients, recipe, staples=()):
    """Tek bir tarifi, evdeki malzemelerle karşılaştırır.

    my_ingredients: malzeme adları listesi ya da {ad: (miktar, birim)} sözlüğü.
    staples: her zaman var sayılan temel malzemeler (tuz, yağ...). Bunlar
             eşleşme oranına katılmaz, eksik sayılmaz.
    """
    if isinstance(my_ingredients, dict):
        pantry = {normalize(k): v for k, v in my_ingredients.items()}
    else:
        pantry = {normalize(item): None for item in my_ingredients}
    staple_set = {normalize(s): None for s in staples}

    have, missing, insufficient, staples_used = [], [], [], []

    for item in recipe["ingredients"]:
        # Malzeme ya düz metin ya da {"name":..., "quantity":..., "unit":...}
        if isinstance(item, dict):
            name = normalize(item["name"])
            quantity, unit = item.get("quantity"), item.get("unit")
        else:
            name = normalize(item)
            quantity, unit = None, None

        if find_in_pantry(name, staple_set) is not None:
            staples_used.append(name)
            continue

        entry = {"name": name, "quantity": quantity, "unit": unit}
        pantry_key = find_in_pantry(name, pantry)

        if pantry_key is None:
            missing.append(entry)
        elif _enough(pantry[pantry_key], quantity, unit):
            have.append(name)
        else:
            have.append(name)
            insufficient.append(entry)

    counted = len(have) + len(missing)
    ratio = len(have) / counted if counted else 1.0

    return {
        "recipe": recipe,
        "have": have,
        "missing": missing,
        "insufficient": insufficient,  # var ama yetersiz
        "staples": staples_used,  # temel malzeme olarak sayılanlar
        "ratio": ratio,
    }


def match_recipes(my_ingredients, recipes, staples=()):
    """Tüm tarifleri eşleştirir ve eşleşme oranı yüksek olandan düşüğe sıralar."""
    results = [match_recipe(my_ingredients, recipe, staples) for recipe in recipes]
    return sorted(results, key=lambda result: result["ratio"], reverse=True)