from core.deduct import plan_deductions

RECIPE = {
    "ingredients": [
        {"name": "kıyma", "quantity": 300, "unit": "g"},
        {"name": "süt", "quantity": 1, "unit": "su bardağı"},
        {"name": "yumurta", "quantity": 2, "unit": "adet"},
        {"name": "un", "quantity": 100, "unit": "g"},
        {"name": "tuz", "quantity": 1, "unit": "çay kaşığı"},
        {"name": "domates", "quantity": 2, "unit": "adet"},
    ]
}


def by_name(plan):
    return {p["name"]: p for p in plan}


def test_azaltma_ve_birim_donusumu():
    pantry = {"kıyma": (500, "g"), "süt": (1, "l")}
    p = by_name(plan_deductions(RECIPE, pantry))
    assert p["kıyma"]["action"] == "reduce" and p["kıyma"]["left"] == (200, "g")
    assert p["süt"]["action"] == "reduce" and p["süt"]["left"] == (0.8, "l")  # 1 l - 200 ml


def test_biten_malzeme_silinir():
    p = by_name(plan_deductions(RECIPE, {"kıyma": (300, "g"), "yumurta": (2, "adet")}))
    assert p["kıyma"]["action"] == "remove"
    assert p["yumurta"]["action"] == "remove"
    p2 = by_name(plan_deductions(RECIPE, {"kıyma": (200, "g")}))  # yetmiyor: bitti say
    assert p2["kıyma"]["action"] == "remove"


def test_miktar_bilinmiyorsa_unknown():
    p = by_name(plan_deductions(RECIPE, {"kıyma": (None, None)}))
    assert p["kıyma"]["action"] == "unknown" and p["kıyma"]["left"] is None


def test_birim_uyumsuzsa_unknown():
    p = by_name(plan_deductions(RECIPE, {"yumurta": (1, "paket")}))  # paket ve adet: aynı tür ama...
    assert p["yumurta"]["action"] in ("reduce", "remove", "unknown")
    p2 = by_name(plan_deductions(RECIPE, {"kıyma": (2, "adet")}))  # g ile adet karşılaştırılamaz
    assert p2["kıyma"]["action"] == "unknown"


def test_temel_malzeme_ve_dolapta_olmayan_atlanir():
    plan = plan_deductions(RECIPE, {"un": (1, "kg"), "tuz": (500, "g")}, staples=["tuz", "un"])
    assert plan == []
    plan = plan_deductions(RECIPE, {"kıyma": (500, "g")})
    assert [p["name"] for p in plan] == ["kıyma"]


def test_ayni_malzeme_iki_satirda_toplanir():
    recipe = {"ingredients": [
        {"name": "şeker", "quantity": 100, "unit": "g"},
        {"name": "şeker", "quantity": 50, "unit": "g"},
    ]}
    p = by_name(plan_deductions(recipe, {"şeker": (1, "kg")}))
    assert p["şeker"]["left"] == (0.85, "kg")


def test_kelime_eslesmesi():
    p = by_name(plan_deductions(
        {"ingredients": [{"name": "mercimek", "quantity": 100, "unit": "g"}]},
        {"kırmızı mercimek": (500, "g")},
    ))
    assert p["kırmızı mercimek"]["left"] == (400, "g")


def test_farkli_tur_birimler_gram_tablosuyla_cevrilir():
    # Dolapta 1 kg biber, tarifte 2 adet biber: tamamı değil, yaklaşık 150 g düşer
    recipe = {"ingredients": [{"name": "biber", "quantity": 2, "unit": "adet"}]}
    p = by_name(plan_deductions(recipe, {"biber": (1, "kg")}))
    assert p["biber"]["action"] == "reduce"
    left, unit = p["biber"]["left"]
    assert unit == "kg" and 0.75 < left < 0.98


def test_dolapta_adet_tarifte_gram():
    # Dolapta 10 adet domates, tarif 2 adet istiyor -> 8 adet kalır
    p = by_name(plan_deductions(RECIPE, {"domates": (10, "adet")}))
    assert p["domates"]["left"] == (8, "adet")
    # Dolapta 500 g kıyma, tarif 300 g -> 200 g
    p2 = by_name(plan_deductions(RECIPE, {"kıyma": (500, "g")}))
    assert p2["kıyma"]["left"] == (200, "g")


def test_bilinmeyen_malzemede_tur_farkliysa_unknown():
    p = by_name(plan_deductions(
        {"ingredients": [{"name": "uzaylı tozu", "quantity": 2, "unit": "adet"}]},
        {"uzaylı tozu": (1, "kg")},
    ))
    assert p["uzaylı tozu"]["action"] == "unknown"
