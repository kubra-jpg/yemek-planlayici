import json
from pathlib import Path

from core.texts import describe, load_texts, tip_for

DATA = Path(__file__).parent.parent / "data"


def test_her_tarifin_tanitimi_ve_pufu_var():
    recipes = json.loads((DATA / "recipes.json").read_text(encoding="utf-8"))
    texts = load_texts(DATA / "texts.json")
    eksik = [r["name"] for r in recipes if not describe(r["name"], texts)]
    assert not eksik, eksik[:5]
    assert all(tip_for(r["name"], texts) for r in recipes)


def test_adimlar_aciklayici():
    recipes = json.loads((DATA / "recipes.json").read_text(encoding="utf-8"))
    steps = [s for r in recipes for s in r["steps"]]
    ortalama = sum(len(s) for s in steps) / len(steps)
    assert ortalama > 90, ortalama
    assert all(len(r["steps"]) >= 2 for r in recipes)


def test_bilinmeyen_tarif_bos_doner():
    assert describe("Olmayan tarif", {}) == ""
    assert load_texts(DATA / "yok.json") == {}
