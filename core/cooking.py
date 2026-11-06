"""Pişirme modu için saf mantık: porsiyon ölçekleme ve pişirme sonrası dolap güncellemesi."""

from core.matcher import find_in_pantry, normalize
from core.units import format_amount

# Birim -> yuvarlama adımı (ölçeklenmiş miktar bu adımın katına yuvarlanır)
_STEP = {
    "yemek kaşığı": 0.25,
    "tatlı kaşığı": 0.25,
    "çay kaşığı": 0.25,
    "su bardağı": 0.25,
    "kg": 0.05,
    "l": 0.05,
    "adet": 0.5,
    "dilim": 1,
    "demet": 0.5,
    "paket": 0.5,
}


def scale_quantity(quantity, unit, factor):
    """Miktarı factor ile çarpıp mutfakta okunabilir bir değere yuvarlar.

    g/ml: 50 ve üzeri 5'in katına, altı tam sayıya; kaşık/bardak: çeyrek;
    adet/demet/paket: yarım; hiçbir miktar 0'a düşmez (en az bir adım).
    """
    if quantity is None:
        return None
    raw = quantity * factor
    if unit in ("g", "ml"):
        value = round(raw / 5) * 5 if raw >= 50 else round(raw)
        return max(value, 1)
    step = _STEP.get(unit)
    if step is None:
        return round(raw, 2)
    value = round(raw / step) * step
    value = max(value, step)
    return int(value) if value == int(value) else round(value, 2)


def _tr_number(value):
    """1.5 -> '1,5' (Türkçe ondalık ayracı)."""
    if value is None:
        return ""
    if float(value) == int(float(value)):
        return str(int(value))
    return str(round(float(value), 2)).replace(".", ",")


def _label(name, quantity, unit):
    amount = format_amount(quantity, unit) if quantity is not None else ""
    amount = amount.replace(".", ",") if amount else ""
    return f"{name} ({amount})" if amount else name


# Adım metinlerinde miktar yazılırken kullanılan birim adları
_UNIT_TEXT = {"l": "litre"}


def _amount_text(name, quantity, unit):
    """Adım metinlerindeki yazımla aynı miktar ifadesi: '2 domates', '500 g kıyma'."""
    if not quantity:
        return None
    if unit in (None, "", "adet"):
        return f"{_tr_number(quantity)} {name}"
    return f"{_tr_number(quantity)} {_UNIT_TEXT.get(unit, unit)} {name}"


def scale_steps(steps, ingredients, factor):
    """Adım metinlerindeki malzeme miktarlarını kişi sayısına göre günceller.

    Adımlar '2 domates', '0,5 su bardağı pirinç' gibi miktarları tarifteki yazımla
    içerir; her malzeme için bu ifade bulunup ölçeklenmiş hâliyle değiştirilir.
    Eşleşme bulunamayan metinlere dokunulmaz.
    """
    if factor == 1:
        return list(steps)
    swaps = []
    for ing in ingredients:
        old = _amount_text(ing["name"], ing.get("quantity"), ing.get("unit"))
        if not old:
            continue
        new = _amount_text(
            ing["name"],
            scale_quantity(ing.get("quantity"), ing.get("unit"), factor),
            ing.get("unit"),
        )
        if new and new != old:
            swaps.append((old, new))
    swaps.sort(key=lambda pair: len(pair[0]), reverse=True)  # uzun ifadeyi önce değiştir
    out = []
    for step in steps:
        for old, new in swaps:
            if old in step:
                step = step.replace(old, new)
            elif old[:1].upper() + old[1:] in step:
                step = step.replace(old[:1].upper() + old[1:], new[:1].upper() + new[1:])
        out.append(step)
    return out


def scale_recipe(recipe, servings):
    """Tarifin kopyasını verilen kişi sayısına göre ölçekler (orijinale dokunmaz)."""
    base = max(int(recipe.get("servings") or 1), 1)
    factor = servings / base
    ingredients = []
    for ing in recipe["ingredients"]:
        quantity = scale_quantity(ing.get("quantity"), ing.get("unit"), factor)
        ingredients.append(
            {
                **ing,
                "quantity": quantity,
                "label": _label(ing["name"], quantity, ing.get("unit")),
            }
        )
    return {
        **recipe,
        "servings": servings,
        "ingredients": ingredients,
        "steps": scale_steps(recipe.get("steps", []), recipe["ingredients"], factor),
    }


def used_pantry_names(result, pantry, staples=()):
    """Pişirmede kullanılan, dolaptaki malzemelerin dolap adları (temel malzemeler hariç).

    result: match_recipe çıktısı; pantry: {ad: ...}; dönüş: tekrarsız, tarif sırasında liste.
    """
    original = {normalize(name): name for name in pantry}
    staple_set = {normalize(s): None for s in staples}
    used = []
    for name in result["have"]:
        if find_in_pantry(normalize(name), staple_set) is not None:
            continue
        key = find_in_pantry(normalize(name), original)
        if key is not None and original[key] not in used:
            used.append(original[key])
    return used
