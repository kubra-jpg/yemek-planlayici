"""Pişirme sonrası akıllı dolap düşümü: tarifte kullanılan miktarı dolaptaki miktardan düşer."""

from core.matcher import find_in_pantry, normalize
from core.nutrition import grams
from core.units import UNITS, is_comparable, to_base


def _round_for(unit, value):
    """Kalan miktarı birime uygun yuvarlar (g/ml tam sayı, diğerleri 2 ondalık)."""
    if unit and unit.strip().lower() in ("g", "gram", "ml"):
        return int(round(value))
    value = round(value, 2)
    return int(value) if value == int(value) else value


def _convert(name, quantity, unit, target_unit):
    """quantity+unit miktarını target_unit cinsine çevirir; çevrilemezse None.

    Birimler aynı türdense (g-kg, ml-l, adet-dilim) doğrudan çevrilir. Tür farklıysa
    (dolapta 1 kg biber, tarifte 2 adet biber) malzemenin gram tablosu kullanılır.
    """
    if quantity is None or not unit or not target_unit:
        return None
    if is_comparable(unit, target_unit):
        base = to_base(quantity, unit)
        return None if base is None else base / UNITS[target_unit.strip().lower()][1]
    used_g = grams(name, quantity, unit)
    per_target = grams(name, 1, target_unit)
    if used_g is None or not per_target:
        return None
    return used_g / per_target


def plan_deductions(scaled_recipe, pantry, staples=()):
    """Tarifte kullanılan malzemeleri dolapla eşleştirip düşüm önerisi çıkarır.

    scaled_recipe: porsiyona göre ölçeklenmiş tarif (scale_recipe çıktısı).
    pantry: {dolap adı: (miktar, birim)}; miktar/birim None olabilir.
    staples: her zaman evde sayılan temel malzemeler (düşülmez).

    Her öneri: {"name": dolap adı, "action": ..., "have": (miktar, birim),
    "used": (miktar, birim) ya da None, "left": (miktar, birim) ya da None}
    action değerleri:
      "reduce"  -> miktar yeterli; "left" kadar kalır
      "remove"  -> kullanılan miktar dolaptakini bitiriyor (ya da aşıyor)
      "unknown" -> dolaptaki miktar bilinmiyor ya da birimler karşılaştırılamıyor;
                   kullanıcı elle 'bitti' diyebilir
    """
    original = {normalize(name): name for name in pantry}
    normalized = {normalize(name): value for name, value in pantry.items()}
    staple_set = {normalize(s): None for s in staples}

    used_in_unit = {}  # dolap adı (normalize) -> kullanılan miktar (dolabın birimiyle)
    touched = []  # tarif sırasında, tekrarsız
    unknown_use = set()  # birimi karşılaştırılamayan kullanımlar

    for ing in scaled_recipe["ingredients"]:
        name = normalize(ing["name"])
        if find_in_pantry(name, staple_set) is not None:
            continue
        key = find_in_pantry(name, normalized)
        if key is None:
            continue
        if key not in touched:
            touched.append(key)
        have_q, have_u = normalized[key] or (None, None)
        need_q, need_u = ing.get("quantity"), ing.get("unit")
        used = _convert(ing["name"], need_q, need_u, have_u) if have_q is not None else None
        if used is None:
            unknown_use.add(key)
            continue
        used_in_unit[key] = used_in_unit.get(key, 0.0) + used

    plan = []
    for key in touched:
        have_q, have_u = normalized[key] or (None, None)
        entry = {"name": original[key], "have": (have_q, have_u), "used": None, "left": None}
        if key in unknown_use or key not in used_in_unit:
            entry["action"] = "unknown"
        else:
            used = used_in_unit[key]
            left = have_q - used
            entry["used"] = (_round_for(have_u, used), have_u)
            if left <= 1e-9:
                entry["action"] = "remove"
            else:
                entry["action"] = "reduce"
                entry["left"] = (_round_for(have_u, left), have_u)
                if entry["left"][0] <= 0:  # yuvarlama sonrası sıfıra düştüyse bitti say
                    entry["action"] = "remove"
                    entry["left"] = None
        plan.append(entry)
    return plan
