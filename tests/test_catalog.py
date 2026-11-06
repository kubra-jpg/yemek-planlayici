from core.catalog import CATALOG, PRESETS, catalog_groups, catalog_names
from core.matcher import normalize
from core.staples import STAPLE_CANDIDATES


def test_catalog_is_large_and_normalized():
    names = catalog_names()
    assert len(names) > 250
    assert all(normalize(n) == n for n in names)
    assert len(names) == len(set(names))


def test_staples_are_in_catalog():
    assert set(STAPLE_CANDIDATES) <= set(catalog_names())


def test_every_category_has_items():
    assert all(CATALOG[k] for k in CATALOG)


def test_every_recipe_ingredient_is_in_catalog():
    import json
    from pathlib import Path

    data = json.loads((Path(__file__).parent.parent / "data" / "recipes.json").read_text(encoding="utf-8"))
    names = set(catalog_names())
    missing = {i["name"] for r in data for i in r["ingredients"]} - names
    assert not missing, sorted(missing)


def test_groups_have_no_duplicates_across_categories():
    groups = catalog_groups()
    flat = [n for items in groups.values() for n in items]
    assert len(flat) == len(set(flat))
    assert set(flat) == set(catalog_names())


def test_presets_exist_in_catalog():
    names = set(catalog_names())
    for label, items in PRESETS.items():
        assert items and set(items) <= names, label
