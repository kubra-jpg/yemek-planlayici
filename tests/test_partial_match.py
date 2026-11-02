from core.matcher import find_in_pantry, match_recipe

SOUP = {
    "id": 1,
    "name": "Mercimek çorbası",
    "ingredients": [
        {"name": "kırmızı mercimek", "quantity": 200, "unit": "g"},
        {"name": "soğan", "quantity": 1, "unit": "adet"},
    ],
}


def test_generic_pantry_item_matches_specific_recipe_item():
    assert find_in_pantry("kırmızı mercimek", {"mercimek": None}) == "mercimek"


def test_specific_pantry_item_matches_generic_recipe_item():
    assert find_in_pantry("mercimek", {"kırmızı mercimek": None}) == "kırmızı mercimek"


def test_exact_match_is_preferred():
    pantry = {"mercimek": None, "kırmızı mercimek": None}
    assert find_in_pantry("kırmızı mercimek", pantry) == "kırmızı mercimek"


def test_different_words_do_not_match():
    assert find_in_pantry("zeytinyağı", {"yağ": None}) is None
    assert find_in_pantry("ton balığı", {"balık": None}) is None


def test_soup_matches_with_generic_lentil():
    result = match_recipe({"mercimek": (None, None)}, SOUP)
    assert result["have"] == ["kırmızı mercimek"]
    assert result["ratio"] == 0.5


def test_partial_match_checks_quantity():
    result = match_recipe({"mercimek": (100, "g"), "soğan": (2, "adet")}, SOUP)
    assert [i["name"] for i in result["insufficient"]] == ["kırmızı mercimek"]