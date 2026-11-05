from core.goals import filter_by_goals, sort_by_nutrition


def make(name, ingredients, servings=1, ratio=1.0):
    return {
        "recipe": {"name": name, "time_min": 10, "servings": servings, "ingredients": ingredients},
        "ratio": ratio,
    }


LIGHT = make("Salata", [{"name": "salatalık", "quantity": 200, "unit": "g"}])
EGGS = make("Yumurta", [{"name": "yumurta", "quantity": 4, "unit": "adet"}])  # ~315 kcal, 28 g protein
CHICKEN = make("Tavuk", [{"name": "tavuk göğsü", "quantity": 200, "unit": "g"}])  # ~330 kcal, 62 g protein
RESULTS = [LIGHT, EGGS, CHICKEN]


def names(results):
    return [r["recipe"]["name"] for r in results]


def test_no_goals_keeps_everything():
    assert names(filter_by_goals(RESULTS)) == ["Salata", "Yumurta", "Tavuk"]


def test_max_kcal_filter():
    assert names(filter_by_goals(RESULTS, max_kcal=100)) == ["Salata"]


def test_min_protein_filter():
    assert names(filter_by_goals(RESULTS, min_protein=40)) == ["Tavuk"]


def test_both_filters_together():
    assert filter_by_goals(RESULTS, max_kcal=100, min_protein=40) == []


def test_servings_divide_the_values():
    big = make("Büyük", [{"name": "tavuk göğsü", "quantity": 400, "unit": "g"}], servings=4)
    assert filter_by_goals([big], min_protein=40) == []
    assert filter_by_goals([big], min_protein=30) == [big]


def test_sort_by_kcal_and_protein():
    assert names(sort_by_nutrition(RESULTS, "kcal"))[0] == "Salata"
    assert names(sort_by_nutrition(RESULTS, "protein"))[0] == "Tavuk"


def test_unknown_sort_key_raises():
    import pytest

    with pytest.raises(ValueError):
        sort_by_nutrition(RESULTS, "boyut")