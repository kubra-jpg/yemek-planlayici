import json
from pathlib import Path

from core.equipment import (
    PROFILES,
    TOOLS,
    can_make,
    filter_by_equipment,
    infer_tools,
    load_overrides,
    tools_for,
)

ROOT = Path(__file__).parent.parent


def recipe(name, *steps):
    return {"name": name, "steps": list(steps)}


def test_infer_oven_and_stove_from_steps():
    assert infer_tools(recipe("A", "Fırında pişir.")) == ["fırın"]
    assert infer_tools(recipe("B", "Soğanı kavur.", "Fırınla.")) == ["ocak", "fırın"]
    assert infer_tools(recipe("C", "Kavur.")) == ["ocak"]


def test_infer_grill_blender_and_no_cooking():
    assert infer_tools(recipe("D", "Izgarada pişir.")) == ["ızgara"]
    assert infer_tools(recipe("E", "Blenderdan geçir.")) == ["blender"]
    assert infer_tools(recipe("F", "Doğra.", "Karıştır.")) == []


def test_override_beats_inference_and_is_case_insensitive():
    overrides = {"kek": ["fırın"]}
    assert tools_for(recipe("Kek", "Pişir."), overrides) == ["fırın"]
    assert tools_for(recipe("Başka", "Pişir."), overrides) == ["ocak"]


def test_can_make():
    assert can_make([], [])
    assert can_make(["ocak"], ["ocak", "fırın"])
    assert not can_make(["ocak", "fırın"], ["ocak"])


def test_filter_by_equipment():
    results = [
        {"recipe": recipe("Salata", "Karıştır.")},
        {"recipe": recipe("Menemen", "Kavur.")},
        {"recipe": recipe("Kek", "Fırınla.")},
    ]
    kept = filter_by_equipment(results, ["ocak"])
    assert [r["recipe"]["name"] for r in kept] == ["Salata", "Menemen"]


def test_profiles_use_known_tools():
    for tools in PROFILES.values():
        assert tools is None or set(tools) <= set(TOOLS)


def test_bundled_equipment_file_covers_every_recipe():
    recipes = json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
    overrides = load_overrides()
    names = {r["name"] for r in recipes}
    from core.matcher import normalize

    assert {normalize(n) for n in names} <= set(overrides)
    for tools in overrides.values():
        assert set(tools) <= set(TOOLS)


def test_missing_file_gives_empty_overrides(tmp_path):
    assert load_overrides(tmp_path / "yok.json") == {}
