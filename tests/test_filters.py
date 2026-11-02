from core.filters import filter_recipes, sort_results, turkish_key

RECIPES = [
    {
        "id": 1, "name": "Fırında balık", "time_min": 35, "is_favorite": True,
        "ingredients": [{"name": "balık"}, {"name": "limon"}],
    },
    {
        "id": 2, "name": "Mercimek çorbası", "time_min": 35, "is_favorite": False,
        "ingredients": [{"name": "kırmızı mercimek"}, {"name": "soğan"}],
    },
    {
        "id": 3, "name": "Omlet", "time_min": 10, "is_favorite": False,
        "ingredients": [{"name": "yumurta"}],
    },
]


def names(recipes):
    return [r["name"] for r in recipes]


def test_search_by_recipe_name():
    assert names(filter_recipes(RECIPES, "çorba")) == ["Mercimek çorbası"]


def test_search_by_ingredient():
    assert names(filter_recipes(RECIPES, "BALIK")) == ["Fırında balık"]


def test_empty_query_returns_all():
    assert len(filter_recipes(RECIPES, "")) == 3


def test_max_time():
    assert names(filter_recipes(RECIPES, max_time=15)) == ["Omlet"]


def test_favorites_only():
    assert names(filter_recipes(RECIPES, favorites_only=True)) == ["Fırında balık"]


def test_filters_combine():
    assert filter_recipes(RECIPES, "balık", max_time=15) == []


def test_turkish_alphabet_order():
    words = ["Zeytin", "Çorba", "Cacık", "Ispanak", "Omlet", "Ördek"]
    assert sorted(words, key=turkish_key) == [
        "Cacık", "Çorba", "Ispanak", "Omlet", "Ördek", "Zeytin"
    ]


def _results():
    return [
        {"recipe": RECIPES[0], "ratio": 0.5},
        {"recipe": RECIPES[1], "ratio": 1.0},
        {"recipe": RECIPES[2], "ratio": 0.5},
    ]


def test_sort_by_match_then_time():
    ordered = [r["recipe"]["name"] for r in sort_results(_results(), "match")]
    assert ordered == ["Mercimek çorbası", "Omlet", "Fırında balık"]


def test_sort_by_time():
    assert sort_results(_results(), "time")[0]["recipe"]["name"] == "Omlet"


def test_sort_by_name():
    ordered = [r["recipe"]["name"] for r in sort_results(_results(), "name")]
    assert ordered == ["Fırında balık", "Mercimek çorbası", "Omlet"]