import json
from pathlib import Path

from core.diet import (
    ALLERGIES, DIETS, contains_text, filter_by_diet, forbidden_tags,
    ingredient_tags, load_settings, recipe_tags, save_settings,
)

DATA = json.loads((Path(__file__).parent.parent / "data" / "recipes.json").read_text("utf-8"))


def R(*names):
    return {"ingredients": [{"name": n} for n in names]}


def test_temel_etiketler():
    assert ingredient_tags("kıyma") == {"et"}
    assert ingredient_tags("tavuk göğsü") == {"et"}
    assert ingredient_tags("ton balığı") == {"deniz"}
    assert ingredient_tags("kuşbaşı et") == {"et"}
    assert ingredient_tags("yoğurt") == {"süt"}
    assert ingredient_tags("çam fıstığı") == {"kuruyemiş"}
    assert "susam" in ingredient_tags("tahin")


def test_yanlis_eslesmeler_yok():
    assert ingredient_tags("balkabağı") == set()  # bal değil
    assert ingredient_tags("mısır unu") == set()  # glütensiz
    assert ingredient_tags("mısır") == set()
    assert ingredient_tags("domates") == set()
    assert ingredient_tags("kuru fasulye") == set()


def test_gluten():
    assert "gluten" in ingredient_tags("un")
    assert "gluten" in ingredient_tags("galeta unu")
    assert "gluten" in ingredient_tags("soya sosu")


def test_vejetaryen_vegan():
    veg = filter_by_diet([R("domates", "yumurta"), R("kıyma", "soğan"), R("levrek")], "Vejetaryen")
    assert len(veg) == 1
    assert filter_by_diet([R("domates", "yumurta"), R("domates", "zeytinyağı")], "Vegan") == [R("domates", "zeytinyağı")]
    assert filter_by_diet([R("kıyma"), R("levrek")], "Pesketaryen") == [R("levrek")]


def test_alerji():
    out = filter_by_diet([R("süt", "un"), R("domates")], "Fark etmez", ["Süt"])
    assert out == [R("domates")]
    assert forbidden_tags("Vegan", ["Gluten"]) >= {"gluten", "et", "süt"}


def test_filtre_yoksa_hepsi_gelir():
    assert filter_by_diet(DATA) == DATA


def test_paketli_tarif_sayilari_makul():
    assert 0 < len(filter_by_diet(DATA, "Vegan")) < len(filter_by_diet(DATA, "Vejetaryen")) < len(DATA)
    # vegan tarifler hiçbir hayvansal etiket taşımamalı
    for r in filter_by_diet(DATA, "Vegan"):
        assert not recipe_tags(r) & DIETS["Vegan"]


def test_icerir_metni():
    assert contains_text(R("süt", "un")) == "süt ürünü, gluten"
    assert contains_text(R("domates")) == ""


def test_ayar_kaydet_oku(tmp_path):
    f = tmp_path / "d.json"
    save_settings(f, {"diet": "Vegan", "allergies": ["Süt", "Uydurma"]})
    assert load_settings(f) == {"diet": "Vegan", "allergies": ["Süt"]}
    assert load_settings(tmp_path / "yok.json") == {"diet": "Fark etmez", "allergies": []}
    assert set(ALLERGIES)  # boş değil
