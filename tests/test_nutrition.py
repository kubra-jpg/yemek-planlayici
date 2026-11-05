import json
from pathlib import Path

from core.nutrition import grams, ingredient_kcal, lookup, recipe_calories


def test_unit_conversions():
    assert grams("süt", 1, "su bardağı") == 245
    assert grams("un", 2, "yemek kaşığı") == 125 * 0.075 * 2
    assert grams("yumurta", 2, "adet") == 110
    assert grams("tuz", 1, "çay kaşığı") == 290 * 0.025
    assert grams("kıyma", 0.5, "kg") == 500


def test_unconvertible_returns_none():
    assert grams("kıyma", 1, "adet") is None
    assert ingredient_kcal("bilinmeyen malzeme", 100, "g") is None


def test_lookup_falls_back_to_word_subset():
    assert lookup("kaşar peyniri") is None or lookup("kaşar peyniri") == lookup("kaşar")
    assert lookup("tam yağlı süt") == lookup("süt")
    assert lookup("YUMURTA") == lookup("yumurta")


def test_recipe_calories_per_serving():
    recipe = {
        "servings": 2,
        "ingredients": [
            {"name": "yumurta", "quantity": 4, "unit": "adet"},  # 220 g -> 314.6
            {"name": "tuz", "quantity": 1, "unit": "çay kaşığı"},
        ],
    }
    result = recipe_calories(recipe)
    assert result["total"] == 315
    assert result["per_serving"] == 157
    assert result["unknown"] == []


def test_unknown_ingredients_are_reported_not_counted():
    recipe = {
        "servings": 1,
        "ingredients": [
            {"name": "yumurta", "quantity": 2, "unit": "adet"},
            {"name": "ejder meyvesi", "quantity": 1, "unit": "adet"},
        ],
    }
    result = recipe_calories(recipe)
    assert result["unknown"] == ["ejder meyvesi"]
    assert result["total"] == 157


def test_deep_frying_oil_is_mostly_discarded():
    fried = {"servings": 1, "ingredients": [{"name": "yağ", "quantity": 1, "unit": "su bardağı"}]}
    spooned = {"servings": 1, "ingredients": [{"name": "yağ", "quantity": 2, "unit": "yemek kaşığı"}]}
    assert recipe_calories(fried)["total"] < 400
    assert recipe_calories(spooned)["total"] > 250


def test_all_bundled_recipes_have_calories():
    data = json.loads((Path(__file__).parent.parent / "data" / "recipes.json").read_text(encoding="utf-8"))
    for r in data:
        res = recipe_calories(r)
        assert res["unknown"] == [], (r["name"], res["unknown"])
        assert 0 <= res["per_serving"] < 1500, (r["name"], res["per_serving"])


def test_macros_are_consistent_with_calories():
    from core.nutrition import MACROS, NUTRITION

    assert set(MACROS) == set(NUTRITION)
    for name, (protein, carbs, fat) in MACROS.items():
        kcal = NUTRITION[name][0]
        estimate = 4 * protein + 4 * carbs + 9 * fat
        assert abs(estimate - kcal) <= max(15, 0.2 * kcal), name


def test_recipe_nutrition_per_serving_macros():
    from core.nutrition import recipe_nutrition

    recipe = {
        "servings": 2,
        "ingredients": [{"name": "tavuk göğsü", "quantity": 400, "unit": "g"}],
    }
    result = recipe_nutrition(recipe)
    assert result["protein"] == 62  # 400 g * 31 / 100 / 2
    assert result["carbs"] == 0
    assert result["fat"] == 9
    assert result["per_serving"] == 330