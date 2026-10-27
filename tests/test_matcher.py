from core.matcher import normalize, match_recipe, match_recipes

RECIPE = {
    "id": 1,
    "name": "Menemen",
    "ingredients": ["yumurta", "domates", "biber"],
}


def test_normalize_strips_and_lowercases():
    assert normalize("  Domates ") == "domates"


def test_normalize_turkish_i():
    assert normalize("ISPANAK") == "ıspanak"
    assert normalize("İNCİR") == "incir"


def test_full_match():
    result = match_recipe(["yumurta", "domates", "biber"], RECIPE)
    assert result["ratio"] == 1
    assert result["missing"] == []


def test_partial_match():
    result = match_recipe(["yumurta"], RECIPE)
    assert result["have"] == ["yumurta"]
    assert set(result["missing"]) == {"domates", "biber"}


def test_no_match():
    result = match_recipe(["süt"], RECIPE)
    assert result["ratio"] == 0
    assert result["have"] == []


def test_ignores_case_and_spaces():
    result = match_recipe([" Yumurta ", "DOMATES"], RECIPE)
    assert len(result["have"]) == 2


def test_empty_pantry():
    result = match_recipe([], RECIPE)
    assert result["ratio"] == 0
    assert len(result["missing"]) == 3


def test_sorted_by_ratio():
    recipes = [
        {"id": 1, "name": "A", "ingredients": ["x", "y"]},
        {"id": 2, "name": "B", "ingredients": ["x"]},
    ]
    results = match_recipes(["x"], recipes)
    assert results[0]["recipe"]["name"] == "B"
    assert results[1]["recipe"]["name"] == "A"