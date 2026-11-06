"""Haftalık yemek planı: planı dosyaya kaydetme ve plandaki tariflerin malzemelerini birleştirme."""

import json
from pathlib import Path

from core.cooking import _label, scale_recipe
from core.matcher import normalize

DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def empty_plan(servings=2):
    return {"servings": servings, "days": {d: [] for d in DAYS}}


def load_plan(path):
    """Plan dosyasını okur; yoksa ya da bozuksa boş plan döndürür."""
    plan = empty_plan()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        plan["servings"] = max(int(data.get("servings", 2)), 1)
        for d in DAYS:
            plan["days"][d] = [int(i) for i in data.get("days", {}).get(d, [])]
    except (OSError, ValueError, TypeError, AttributeError):
        return empty_plan()
    return plan


def save_plan(path, plan):
    Path(path).write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")


def planned_recipes(plan, recipes_by_id):
    """Plandaki tarifleri (gün sırasıyla, silinmiş tarifler atlanarak) döndürür."""
    found = []
    for d in DAYS:
        for rid in plan["days"].get(d, []):
            if rid in recipes_by_id:
                found.append(recipes_by_id[rid])
    return found


def merged_shopping_recipe(plan, recipes_by_id):
    """Plandaki tüm tariflerin malzemelerini tek sahte tarifte toplar.

    Her tarif plandaki kişi sayısına ölçeklenir; ad + birim aynıysa miktarlar toplanır.
    match_recipe bu sahte tarife verilince tüm hafta için eksikler çıkar.
    """
    servings = plan["servings"]
    totals = {}
    for recipe in planned_recipes(plan, recipes_by_id):
        for ing in scale_recipe(recipe, servings)["ingredients"]:
            key = (normalize(ing["name"]), ing.get("unit"))
            if key in totals:
                if ing.get("quantity") is not None and totals[key]["quantity"] is not None:
                    totals[key]["quantity"] += ing["quantity"]
            else:
                totals[key] = {"name": ing["name"], "quantity": ing.get("quantity"), "unit": ing.get("unit")}
    ingredients = []
    for ing in totals.values():
        q = ing["quantity"]
        if isinstance(q, float):
            q = round(q, 2)
            ing["quantity"] = int(q) if q == int(q) else q
        ing["label"] = _label(ing["name"], ing["quantity"], ing["unit"])
        ingredients.append(ing)
    return {"id": 0, "name": "Haftalık plan", "servings": servings, "ingredients": ingredients, "steps": []}
