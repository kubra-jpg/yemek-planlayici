from core.cooking import scale_quantity, scale_recipe, used_pantry_names

RECIPE = {
    "name": "Menemen",
    "servings": 2,
    "ingredients": [
        {"name": "yumurta", "quantity": 4, "unit": "adet"},
        {"name": "domates", "quantity": 3, "unit": "adet"},
        {"name": "yağ", "quantity": 2, "unit": "yemek kaşığı"},
        {"name": "kıyma", "quantity": 250, "unit": "g"},
        {"name": "tuz", "quantity": None, "unit": None},
    ],
}


def test_scale_quantity_rounding_by_unit():
    assert scale_quantity(250, "g", 1.5) == 375
    assert scale_quantity(30, "g", 0.3) == 9  # 50 altı: tam sayı
    assert scale_quantity(3, "adet", 1.5) == 4.5
    assert scale_quantity(1, "yemek kaşığı", 0.3) == 0.25  # en az bir adım
    assert scale_quantity(1, "su bardağı", 1.5) == 1.5
    assert scale_quantity(None, "g", 2) is None


def test_scale_recipe_doubles_everything():
    scaled = scale_recipe(RECIPE, 4)
    quantities = {i["name"]: i["quantity"] for i in scaled["ingredients"]}
    assert quantities == {"yumurta": 8, "domates": 6, "yağ": 4, "kıyma": 500, "tuz": None}
    assert scaled["servings"] == 4


def test_scale_recipe_builds_labels_and_keeps_original():
    scaled = scale_recipe(RECIPE, 4)
    labels = {i["name"]: i["label"] for i in scaled["ingredients"]}
    assert labels["yumurta"] == "yumurta (8 adet)"
    assert labels["tuz"] == "tuz"
    assert RECIPE["ingredients"][0]["quantity"] == 4 and RECIPE["servings"] == 2


def test_scale_to_same_servings_is_identity():
    scaled = scale_recipe(RECIPE, 2)
    assert [i["quantity"] for i in scaled["ingredients"]] == [4, 3, 2, 250, None]


def test_used_pantry_names_maps_recipe_names_to_pantry_and_skips_staples():
    result = {"have": ["mercimek", "tuz", "domates"]}
    pantry = {"kırmızı mercimek": (None, None), "domates": (None, None), "tuz": (None, None)}
    assert used_pantry_names(result, pantry, staples=["tuz"]) == ["kırmızı mercimek", "domates"]


def test_used_pantry_names_has_no_duplicates():
    result = {"have": ["mercimek", "kırmızı mercimek"]}
    pantry = {"kırmızı mercimek": (None, None)}
    assert used_pantry_names(result, pantry) == ["kırmızı mercimek"]


# --- Adım metinlerindeki miktarların ölçeklenmesi ---
RECIPE_STEPS = {
    "name": "Menemen",
    "servings": 4,
    "ingredients": [
        {"name": "domates", "quantity": 4, "unit": "adet"},
        {"name": "biber", "quantity": 2, "unit": "adet"},
        {"name": "kıyma", "quantity": 500, "unit": "g"},
        {"name": "süt", "quantity": 1, "unit": "su bardağı"},
        {"name": "tuz", "quantity": None, "unit": None},
    ],
    "steps": [
        "4 domates rendeleyip ekle ve 3 dakika pişir.",
        "2 biber ve 500 g kıyma ile birlikte kavur.",
        "1 su bardağı süt ekle; 10 dakika pişir.",
        "Tuzunu tadarak ayarla.",
    ],
}


def test_adimlar_kisi_sayisina_gore_olceklenir():
    scaled = scale_recipe(RECIPE_STEPS, 2)
    assert scaled["steps"][0].startswith("2 domates")
    assert "1 biber" in scaled["steps"][1] and "250 g kıyma" in scaled["steps"][1]
    assert "0,5 su bardağı süt" in scaled["steps"][2]
    assert scaled["steps"][3] == "Tuzunu tadarak ayarla."
    # süreler değişmez
    assert "3 dakika" in scaled["steps"][0] and "10 dakika" in scaled["steps"][2]


def test_ayni_kisi_sayisinda_adimlar_degismez():
    assert scale_recipe(RECIPE_STEPS, 4)["steps"] == RECIPE_STEPS["steps"]


def test_buyutme_de_calisir():
    scaled = scale_recipe(RECIPE_STEPS, 8)
    assert "8 domates" in scaled["steps"][0] and "1000 g kıyma" in scaled["steps"][1]
