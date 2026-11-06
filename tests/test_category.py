import json
from pathlib import Path

from core.category import CATEGORIES, category_of, filter_by_category


def test_ornekler():
    assert category_of("Menemen") == "Kahvaltı"
    assert category_of("Peynirli tost") == "Kahvaltı"
    assert category_of("Pankek") == "Kahvaltı"
    assert category_of("Mercimek çorbası") == "Yemek"
    assert category_of("Keşkek") == "Yemek"
    assert category_of("Fırında tatlı patates") == "Yemek"
    assert category_of("Sütlaç") == "Tatlı"
    assert category_of("Havuçlu kek") == "Tatlı"
    assert category_of("Tatlı patates çorbası") == "Yemek"


def test_filtre():
    recipes = [{"name": "Menemen"}, {"name": "Kuru fasulye"}, {"name": "Baklava"}]
    assert [r["name"] for r in filter_by_category(recipes, "Kahvaltı")] == ["Menemen"]
    assert len(filter_by_category(recipes, "Tümü")) == 3
    assert len(filter_by_category(recipes, None)) == 3


def test_iceceksiz_ve_dengeli():
    data = json.loads((Path(__file__).parent.parent / "data" / "recipes.json").read_text(encoding="utf-8"))
    names = {r["name"] for r in data}
    for drink in ("Ayran", "Bitki çayı", "Sıcak süt balli", "Türk kahvesi", "Limonata"):
        assert drink not in names
    counts = {c: sum(category_of(r["name"]) == c for r in data) for c in CATEGORIES}
    assert all(v >= 50 for v in counts.values()), counts
